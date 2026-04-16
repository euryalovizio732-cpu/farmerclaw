"""
api_smoke_test.py — 接口冒烟测试
所有接口返回格式：{ code:0, message:"...", data:{...} }
逐一打所有注册路由的核心端点，检查：
  - HTTP 状态码是否 200/422
  - data 层是否有预期字段
  - 是否有服务端 500 错误
  - 关键内容质量（伪造数字/占位符/误判）
"""
import httpx, json, sys

BASE = "http://localhost:8001"
TIMEOUT = 90

OK   = "\033[92m✅\033[0m"
FAIL = "\033[91m❌\033[0m"
WARN = "\033[93m⚠️\033[0m"

results = []

def hit(method, path, body=None, expected_status=200, check_keys=None, label=None):
    """返回 (success, data_dict)。data_dict 是 response.data 层或顶层。"""
    label = label or f"{method} {path}"
    try:
        if method == "GET":
            r = httpx.get(BASE + path, timeout=TIMEOUT)
        else:
            r = httpx.post(BASE + path, json=body, timeout=TIMEOUT)
        ok = r.status_code == expected_status
        raw = {}
        try:
            raw = r.json()
        except Exception:
            pass
        # 统一解包 data 层
        data = raw.get("data", raw) if isinstance(raw, dict) else raw
        missing = []
        if ok and check_keys:
            missing = [k for k in check_keys if k not in data]
            if missing:
                ok = False
        icon = OK if ok else FAIL
        print(f"  {icon}  [{r.status_code}]  {label}")
        if not ok:
            if missing:
                print(f"       缺少字段: {missing}")
            if r.status_code >= 500:
                print(f"       服务端错误: {r.text[:300]}")
            elif r.status_code == 422 and not missing:
                errs = raw.get("detail", raw.get("message", ""))
                print(f"       参数校验失败: {errs}")
        results.append((ok, label))
        return ok, data
    except Exception as e:
        print(f"  {FAIL}  [ERR]  {label}  —  {e}")
        results.append((False, label))
        return False, {}


print("=" * 65)
print("  FarmerClaw API Smoke Test")
print("=" * 65)

# ── 1. 基础健康检查 ──────────────────────────────────────────
print("\n【1. 健康检查】")
hit("GET", "/health", check_keys=["status"])
hit("GET", "/health/ready", check_keys=["status", "checks"])
hit("GET", "/")

# ── 2. 选题 Agent ─────────────────────────────────────────────
print("\n【2. 选题 /api/topic/generate】")
ok, d = hit("POST", "/api/topic/generate",
    body={"product_name": "赣南脐橙", "category": "脐橙", "origin": "江西赣州"},
    check_keys=["today_tip", "topics", "hashtags"],
    label="topic.generate (脐橙)")
if ok and d.get("topics"):
    t = d["topics"][0]
    title = t.get("title", "")
    print(f"       → 第1条标题({len(title)}字)：{title}")
    if len(title) > 20:
        print(f"       {WARN} 标题超20字！")

hit("POST", "/api/topic/generate",
    body={"product_name": "五常稻花香大米", "category": "粮油"},
    check_keys=["today_tip", "topics"],
    label="topic.generate (粮油)")

# 缺参数校验
hit("POST", "/api/topic/generate",
    body={},
    expected_status=422,
    label="topic.generate (缺必填字段 → 422)")

# ── 3. Listing / 口播稿 ──────────────────────────────────────
print("\n【3. Listing /api/listing/generate】")
ok, d = hit("POST", "/api/listing/generate",
    body={
        "product_name": "丹东东港草莓",
        "category": "草莓",
        "origin": "辽宁丹东东港",
        "price": "139元3斤",
        "platform": "douyin"
    },
    check_keys=["title", "selling_points", "video_script"],
    label="listing.generate (草莓)")
if ok:
    script = (d.get("video_script") or {}).get("full_script", "")
    has_fabricated = any(x in script for x in ["最后287单", "最后50单", "最后100单", "全额退款不退货"])
    icon = FAIL if has_fabricated else OK
    print(f"       {icon} 库存伪造检测：{'有伪造库存数字！' if has_fabricated else '无伪造库存数字'}")

hit("POST", "/api/listing/generate",
    body={"product_name": "眉县猕猴桃", "category": "猕猴桃", "platform": "pinduoduo"},
    check_keys=["title", "selling_points"],
    label="listing.generate (猕猴桃·拼多多)")

hit("POST", "/api/listing/generate",
    body={},
    expected_status=422,
    label="listing.generate (缺必填 → 422)")

# ── 4. 合规检查 ───────────────────────────────────────────────
print("\n【4. 合规检查 /api/listing/compliance-check】")
ok_c, d_c = hit("POST", "/api/listing/compliance-check",
    body={"title": "无农残纯天然最好吃苹果治百病！", "content": "无农残，最好，治百病", "platform": "douyin"},
    check_keys=["passed", "issues"],
    label="compliance-check (应不通过)")
if ok_c:
    print(f"       → passed={d_c.get('passed')}  issues_count={len(d_c.get('issues', []))}")
    if d_c.get("passed"):
        print(f"       {WARN} 应不通过但却通过了！合规引擎可能漏检")

ok_c2, d_c2 = hit("POST", "/api/listing/compliance-check",
    body={"title": "赣南脐橙产地直发坏果包赔", "content": "产地直发，不甜退款，现摘现发", "platform": "douyin"},
    check_keys=["passed"],
    label="compliance-check (应通过)")
if ok_c2:
    print(f"       → passed={d_c2.get('passed')}")
    if not d_c2.get("passed"):
        print(f"       {WARN} 合法内容被误判拦截！issues={d_c2.get('issues', [])}")

# ── 5. 痛点分析 ───────────────────────────────────────────────
print("\n【5. 痛点 /api/pain-point/analyze】")
hit("POST", "/api/pain-point/analyze",
    body={
        "product_name": "大连大樱桃",
        "category": "樱桃",
        "platform": "douyin",
        "sales_level": "月销500单"
    },
    check_keys=["product_summary", "top_pain_points"],
    label="pain-point.analyze (樱桃)")

hit("POST", "/api/pain-point/analyze",
    body={},
    expected_status=422,
    label="pain-point.analyze (缺必填 → 422)")

# ── 6. 评论回复 ───────────────────────────────────────────────
print("\n【6. 回复 /api/reply/generate】")
ok, d = hit("POST", "/api/reply/generate",
    body={
        "product_name": "赣南脐橙",
        "comment": "这个甜不甜啊",
        "origin": "江西赣州"
    },
    check_keys=["comment_type", "reply", "risk_level"],
    label="reply.generate (产品咨询)")
if ok:
    ct = d.get("comment_type", "")
    bad = ct in ["好评", "正面"]
    print(f"       {'❌ 甜不甜被误判为好评！' if bad else OK + ' comment_type=' + ct}")

ok2, d2 = hit("POST", "/api/reply/generate",
    body={"product_name": "五常大米", "comment": "米到了发霉了", "origin": "黑龙江五常"},
    check_keys=["comment_type", "urgency", "reply"],
    label="reply.generate (质量投诉)")
if ok2:
    urg = d2.get("urgency", "")
    print(f"       → urgency={urg}  risk_level={d2.get('risk_level', '?')}")

ok_b, d_b = hit("POST", "/api/reply/batch",
    body={
        "product_name": "洛川苹果",
        "comments": ["多久发货", "能不能便宜点", "收到了很甜！"]
    },
    label="reply.batch (3条)")
# data 是 list，不是 {replies: [...]}
if ok_b:
    if isinstance(d_b, list) and len(d_b) == 3:
        print(f"       {OK} data 是3条 list，格式正确")
        results[-1] = (True, results[-1][1])
    elif isinstance(d_b, dict) and "replies" in d_b:
        print(f"       {OK} data.replies 格式正确")
        results[-1] = (True, results[-1][1])
    else:
        print(f"       {FAIL} 格式异常: type={type(d_b).__name__} keys={list(d_b.keys()) if isinstance(d_b, dict) else '—'}")
        results[-1] = (False, results[-1][1])

# ── 7. 今日内容包 ─────────────────────────────────────────────
print("\n【7. 内容包 /api/content-pack/generate】")
ok, d = hit("POST", "/api/content-pack/generate",
    body={
        "product_name": "麻江蓝莓",
        "category": "蓝莓",
        "origin": "贵州麻江",
        "price": "24.9元500克"
    },
    check_keys=["topics", "scripts", "live_modules"],
    label="content-pack.generate (蓝莓)")
if ok:
    topics = d.get("topics", [])
    scripts = d.get("scripts", [])
    modules = d.get("live_modules", {})
    print(f"       → topics:{len(topics)} scripts:{len(scripts)} live_module_types:{list(modules.keys())[:4]}")
    # 检查直播积木是否还有残余占位符
    module_text = json.dumps(modules, ensure_ascii=False)
    placeholders = [x for x in ["[需填写", "{赠品}", "{节省金额}"] if x in module_text]
    if placeholders:
        print(f"       {WARN} 直播积木残余占位符: {placeholders}")
    else:
        print(f"       {OK} 直播积木无残余占位符")

# ── 8. 数据看板 ───────────────────────────────────────────────
print("\n【8. 看板 /api/dashboard/stats】")
hit("GET", "/api/dashboard/stats", check_keys=["total_listings"])

# ── 9. 不存在路由 ─────────────────────────────────────────────
print("\n【9. 404 保护】")
hit("GET", "/api/nonexistent", expected_status=404, label="GET /api/nonexistent → 404")

# ── 汇总 ─────────────────────────────────────────────────────
print("\n" + "=" * 65)
total = len(results)
passed = sum(1 for ok, _ in results if ok)
pct = passed / total * 100 if total else 0
print(f"  结果：{passed}/{total}  通过  ({pct:.0f}%)")
if passed < total:
    print("\n  失败项目：")
    for ok, lbl in results:
        if not ok:
            print(f"    ❌  {lbl}")
print("=" * 65)
sys.exit(0 if passed == total else 1)
