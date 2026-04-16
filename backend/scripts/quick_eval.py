"""快速Agent输出测试"""
import requests

BASE = "http://localhost:8001"


def score_script(text):
    if not text:
        return 0, ["无输出"]
    issues = []
    checks = {
        "口语称呼": any(w in text for w in ["家人", "宝贝", "老铁", "亲"]),
        "产地背书": any(w in text for w in ["产地", "现摘", "江西", "辽宁", "黑龙江", "赣南", "丹东", "五常", "信丰"]),
        "承诺保障": any(w in text for w in ["包赔", "赔", "退款", "承诺", "不甜", "坏果"]),
        "逼单CTA": any(w in text for w in ["下单", "拍", "快", "最后", "限量", "扣1", "点链接"]),
        "价格锚定": any(w in text for w in ["元", "块", "价格", "只要", "直播间", "优惠"]),
        "长度合理": len(text) <= 350,
    }
    for k, v in checks.items():
        if v:
            pass
        else:
            issues.append(f"❌ 缺{k}")
    return sum(checks.values()), issues


def score_topic(title):
    issues = []
    checks = {
        "长度≤20字": len(title) <= 20,
        "无书面语": not any(w in title for w in ["揭秘", "盘点", "全方位", "系列"]),
        "有感官/数字": any(w in title for w in ["甜", "脆", "汁", "香", "烂", "丑", "贵", "斤", "元", "招", "次", "天"]),
        "有语气钩子": any(w in title for w in ["?", "？", "!", "！"]),
    }
    for k, v in checks.items():
        if not v:
            issues.append(f"❌ {k}")
    return sum(checks.values()), issues


def score_reply(reply):
    issues = []
    checks = {
        "口语称呼": any(w in reply for w in ["家人", "宝贝", "亲"]),
        "有处理承诺": any(w in reply for w in ["平台", "退款", "申请", "包赔", "赔", "承诺"]),
        "无推诿": "联系客服" not in reply and "稍后处理" not in reply,
        "有具体行动": any(w in reply for w in ["图", "拍照", "单号", "时间", "规格", "申请"]),
    }
    for k, v in checks.items():
        if not v:
            issues.append(f"❌ {k}")
    return sum(checks.values()), issues


CASES = [
    {"product_name": "赣南脐橙", "category": "水果", "origin": "江西赣州信丰", "specification": "5斤装", "price": "29.9元/5斤"},
    {"product_name": "丹东草莓", "category": "水果", "origin": "辽宁丹东", "specification": "1斤装", "price": "39.9元/斤"},
    {"product_name": "东北大米", "category": "粮油", "origin": "黑龙江五常", "specification": "5斤装", "price": "49.9元/5斤"},
]

print("=" * 60)
print("三农AI Agent 端到端评测")
print("=" * 60)

all_scores = []

for case in CASES:
    pname = case["product_name"]
    print(f"\n{'='*55}")
    print(f"品类: {pname} | {case['origin']}")
    print(f"{'='*55}")

    # ── 1. 口播稿 ──
    payload = {**case, "platform": "douyin"}
    r = requests.post(f"{BASE}/api/listing/generate", json=payload, timeout=60)
    d = r.json().get("data", {})

    vs_raw = d.get("video_script", "")
    ls_raw = d.get("live_script", "")
    vs = vs_raw.get("full_script", "") if isinstance(vs_raw, dict) else vs_raw
    ls = " ".join(str(v) for v in ls_raw.values()) if isinstance(ls_raw, dict) else ls_raw

    print(f"\n[视频口播 {len(vs)}字]")
    print(vs[:350] if vs else "无输出")
    sc, iss = score_script(vs)
    print(f"  评分: {sc}/6  {'✅ 达标' if sc >= 5 else '❌ 未达标'}")
    if iss:
        print("  " + "  ".join(iss))
    all_scores.append(("口播稿", pname, sc, 6))

    print(f"\n[直播话术 {len(ls)}字]")
    print(ls[:350] if ls else "无输出")
    sc2, iss2 = score_script(ls)
    print(f"  评分: {sc2}/6  {'✅ 达标' if sc2 >= 5 else '❌ 未达标'}")
    if iss2:
        print("  " + "  ".join(iss2))
    all_scores.append(("直播话术", pname, sc2, 6))

    # ── 2. 选题 ──
    print(f"\n[选题标题]")
    tp = {"product_name": pname, "category": case["category"], "origin": case["origin"]}
    r2 = requests.post(f"{BASE}/api/topic/generate", json=tp, timeout=30)
    td = r2.json().get("data", r2.json())
    topics = td.get("topics", []) if isinstance(td, dict) else []
    if not topics:
        print("  无输出")
    for t in topics:
        title = t.get("title", "")
        sc3, iss3 = score_topic(title)
        flag = "✅" if sc3 >= 3 else "❌"
        print(f"  {flag}[{t.get('type','')}] {title}  ({sc3}/4)")
        if iss3:
            print("    " + "  ".join(iss3))
    if topics:
        avg = sum(score_topic(t.get("title", ""))[0] for t in topics) / len(topics)
        all_scores.append(("选题标题", pname, avg, 4))

    # ── 3. 回复 ──
    print(f"\n[评论回复]")
    comments = ["收到了全是烂的", "甜不甜啊", "能便宜点吗", "什么时候发货"]
    rp = {"product_name": pname, "origin": case["origin"], "price": case["price"], "comments": comments}
    r3 = requests.post(f"{BASE}/api/reply/batch", json=rp, timeout=30)
    rd = r3.json()
    rlist = rd if isinstance(rd, list) else rd.get("data", rd.get("results", []))
    if not rlist:
        print("  无输出")
    for comment, result in zip(comments, rlist):
        if not isinstance(result, dict):
            continue
        reply = result.get("reply", "")
        sc4, iss4 = score_reply(reply)
        flag = "✅" if sc4 >= 3 else "❌"
        print(f"  {flag} [{result.get('comment_type','')}] 「{comment[:15]}」")
        print(f"     {reply[:100]}")
        if iss4:
            print("     " + "  ".join(iss4))
    if rlist and isinstance(rlist[0], dict):
        avg_r = sum(score_reply(r.get("reply", ""))[0] for r in rlist if isinstance(r, dict)) / len(rlist)
        all_scores.append(("评论回复", pname, avg_r, 4))

    # ── 4. 痛点 ──
    print(f"\n[痛点分析]")
    pp = {"product_name": pname, "category": case["category"], "origin": case["origin"], "price": 29.9}
    r4 = requests.post(f"{BASE}/api/pain-point/analyze", json=pp, timeout=30)
    ppd = r4.json().get("data", r4.json())
    pain_pts = ppd.get("top_pain_points", []) if isinstance(ppd, dict) else []
    pricing = ppd.get("pricing_suggestion", {}) if isinstance(ppd, dict) else {}
    print(f"  痛点数: {len(pain_pts)}")
    for p in pain_pts[:3]:
        if isinstance(p, dict):
            print(f"  [{p.get('severity','')}] {p.get('pain_point','')} — {str(p.get('opportunity',''))[:40]}")
    sp = pricing.get("suggested_price", "") if pricing else ""
    has_real = any(c.isdigit() for c in str(sp))
    print(f"  定价建议: {sp}  {'✅' if has_real else '❌ 无真实价格'}")

print(f"\n{'='*55}")
print("汇总评分:")
for func, prod, sc, mx in all_scores:
    flag = "✅" if sc / mx >= 0.75 else "❌"
    print(f"  {flag} {func}/{prod}: {sc:.1f}/{mx}")
