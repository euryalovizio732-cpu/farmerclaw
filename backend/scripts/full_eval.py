"""全量Agent评测脚本 - 对标检验"""
import requests, json, sys

BASE = "http://localhost:8001"

CASES = [
    {"product_name": "赣南脐橙", "category": "水果", "origin": "江西赣州信丰", "spec": "5斤装", "price": "29.9元/5斤"},
    {"product_name": "丹东草莓", "category": "水果", "origin": "辽宁丹东", "spec": "1斤装", "price": "39.9元/斤"},
    {"product_name": "五常大米", "category": "粮油", "origin": "黑龙江五常", "spec": "5斤装", "price": "49.9元/5斤"},
]


def h(title):
    print(f"\n{'='*58}\n  {title}\n{'='*58}")


def sec(title):
    print(f"\n>> {title}")


def score_video_script(text):
    if not text:
        return 0, ["无输出"]
    issues = []
    checks = {
        "①口语称呼(家人/宝贝)": any(w in text for w in ["家人", "宝贝", "老铁", "亲"]),
        "②产地背书":           any(w in text for w in ["产地", "赣南", "丹东", "五常", "信丰", "江西", "辽宁", "黑龙江", "现摘", "果园"]),
        "③承诺保障(包赔/退款)": any(w in text for w in ["包赔", "赔", "退款", "承诺", "不甜", "坏果"]),
        "④逼单CTA":           any(w in text for w in ["下单", "拍", "手快", "最后", "限量", "只剩", "秒杀"]),
        "⑤价格锚定":           any(w in text for w in ["元", "块", "只要", "优惠", "直播间"]),
        "⑥长度≤350字":        len(text) <= 350,
    }
    for k, v in checks.items():
        if not v:
            issues.append(f"❌ {k}")
    return sum(checks.values()), issues


def score_topic(title):
    issues = []
    checks = {
        "①≤20字":   len(title) <= 20,
        "②无书面语": not any(w in title for w in ["揭秘", "盘点", "全方位", "系列", "深度解析"]),
        "③有钩子词": any(w in title for w in ["甜", "脆", "汁", "香", "烂", "丑", "贵", "斤", "元", "招", "坑", "假"]),
        "④有语气符": any(w in title for w in ["?", "？", "!", "！"]),
    }
    for k, v in checks.items():
        if not v:
            issues.append(f"❌ {k}")
    return sum(checks.values()), issues


def score_reply(reply, comment_type=""):
    issues = []
    is_complaint = any(w in comment_type for w in ["质量", "投诉", "物流", "发货"])
    # 允许顺丰单号SF/快递单号等，仅拦截真正英文句子
    has_real_english = any(
        w in reply for w in [" the ", " is ", " are ", " and ", " of "]
    ) or "guaranteed" in reply.lower()
    checks = {
        "①口语称呼":   any(w in reply for w in ["家人", "宝贝", "亲"]),
        "②有处理承诺": (not is_complaint) or any(w in reply for w in ["平台", "退款", "申请", "包赔", "赔", "处理"]),
        "③无推诿":     "联系客服" not in reply and "稍后处理" not in reply,
        "④无英文":     not has_real_english,
    }
    for k, v in checks.items():
        if not v:
            issues.append(f"❌ {k}")
    return sum(checks.values()), issues


total_scores = []

for case in CASES:
    h(f"{case['product_name']}  |  {case['origin']}")

    # ══════════════════════════════════════════
    # 1. 口播稿 & 直播话术
    # ══════════════════════════════════════════
    sec("口播稿 & 直播话术")
    r = requests.post(f"{BASE}/api/listing/generate", json={
        "product_name": case["product_name"],
        "category": case["category"],
        "origin": case["origin"],
        "specification": case["spec"],
        "price": case["price"],
        "platform": "douyin",
    }, timeout=120)
    d = r.json().get("data", {})

    vs_raw = d.get("video_script", {})
    ls_raw = d.get("live_script", {})
    vs = vs_raw.get("full_script", "") if isinstance(vs_raw, dict) else str(vs_raw)
    ls_text = " ".join(str(v) for v in ls_raw.values()) if isinstance(ls_raw, dict) else str(ls_raw)

    print(f"  标题: {d.get('title','')}")
    print(f"  视频口播({len(vs)}字): {vs[:200]}...")
    sc1, iss1 = score_video_script(vs)
    print(f"  口播评分: {sc1}/6  {'✅' if sc1 >= 5 else '❌'}")
    if iss1:
        print(f"  问题: {' '.join(iss1)}")

    sc2, iss2 = score_video_script(ls_text)
    print(f"  直播话术评分: {sc2}/6  {'✅' if sc2 >= 5 else '❌'}")
    if iss2:
        print(f"  问题: {' '.join(iss2)}")

    total_scores += [("口播稿", case["product_name"], sc1, 6),
                     ("直播话术", case["product_name"], sc2, 6)]

    # ══════════════════════════════════════════
    # 2. 选题生成
    # ══════════════════════════════════════════
    sec("选题生成")
    r2 = requests.post(f"{BASE}/api/topic/generate", json={
        "product_name": case["product_name"],
        "category": case["category"],
        "origin": case["origin"],
    }, timeout=90)
    td = r2.json().get("data", {})
    topics = td.get("topics", []) if isinstance(td, dict) else []
    tip = td.get("today_tip", "") if isinstance(td, dict) else ""
    tags = td.get("hashtags", []) if isinstance(td, dict) else []

    print(f"  今日建议: {tip}")
    topic_scores = []
    for t in topics:
        title = t.get("title", "")
        sc3, iss3 = score_topic(title)
        flag = "✅" if sc3 >= 3 else "❌"
        print(f"  {flag}[{t.get('type','')}] {title}  ({sc3}/4)")
        if iss3:
            print(f"    {' '.join(iss3)}")
        topic_scores.append(sc3)

    if not topics:
        print("  ❌ 无输出")
    else:
        avg_t = sum(topic_scores) / len(topic_scores)
        total_scores.append(("选题标题", case["product_name"], avg_t, 4))

    # ══════════════════════════════════════════
    # 3. 评论回复
    # ══════════════════════════════════════════
    sec("评论回复")
    test_comments = [
        "收到了，全是烂的，坏掉了！",
        "甜不甜啊，好吃吗",
        "能便宜点吗",
        "怎么还没发货",
        "收到了好甜！！！",
    ]
    r3 = requests.post(f"{BASE}/api/reply/batch", json={
        "product_name": case["product_name"],
        "origin": case["origin"],
        "price": case["price"],
        "comments": test_comments,
    }, timeout=90)
    rdata = r3.json()
    replies = rdata if isinstance(rdata, list) else rdata.get("data", [])

    reply_scores = []
    for comment, rep in zip(test_comments, replies):
        if not isinstance(rep, dict):
            continue
        reply = rep.get("reply", "")
        ctype = rep.get("comment_type", "")
        sc4, iss4 = score_reply(reply, ctype)
        flag = "✅" if sc4 >= 3 else "❌"
        short_c = comment[:15]
        short_r = reply[:80]
        print(f"  {flag}[{ctype}] 「{short_c}」")
        print(f"      → {short_r}")
        if iss4:
            print(f"      问题: {' '.join(iss4)}")
        reply_scores.append(sc4)

    if reply_scores:
        avg_r = sum(reply_scores) / len(reply_scores)
        total_scores.append(("评论回复", case["product_name"], avg_r, 4))

    # ══════════════════════════════════════════
    # 4. 痛点分析
    # ══════════════════════════════════════════
    sec("痛点分析")
    r4 = requests.post(f"{BASE}/api/pain-point/analyze", json={
        "category": case["category"],
        "product_name": case["product_name"],
        "platform": "douyin",
    }, timeout=120)
    ppd = r4.json().get("data", {})

    if ppd:
        pain_pts = ppd.get("top_pain_points", [])
        pricing = ppd.get("pricing_suggestion", {})
        print(f"  痛点数: {len(pain_pts)}")
        for p in pain_pts[:3]:
            if isinstance(p, dict):
                sev = p.get("frequency", p.get("severity", ""))
                pt = p.get("pain_point", "")
                opp = p.get("opportunity", "")
                print(f"  [{sev}] {pt[:40]}")
                if opp:
                    print(f"         机会: {str(opp)[:50]}")
        sp = pricing.get("suggested_price_range", pricing.get("suggested_price", "")) if isinstance(pricing, dict) else ""
        has_price = any(c.isdigit() for c in str(sp))
        print(f"  定价建议: {sp}  {'✅' if has_price else '❌ 无数据'}")
        pp_ok = len(pain_pts) >= 3 and has_price
        total_scores.append(("痛点分析", case["product_name"], 4 if pp_ok else 2, 4))
    else:
        print(f"  ❌ 接口错误: {r4.json().get('message','')}")
        total_scores.append(("痛点分析", case["product_name"], 0, 4))

# ══════════════════════════════════════════
# 汇总报告
# ══════════════════════════════════════════
h("汇总对标报告")
print(f"{'功能':<12} {'品类':<10} {'得分':>6}  {'状态'}")
print("-" * 46)

pass_count = 0
total_count = 0
for func, prod, sc, mx in total_scores:
    pct = sc / mx
    flag = "✅ 达标" if pct >= 0.75 else "❌ 未达标"
    print(f"  {func:<10} {prod:<10} {sc:.1f}/{mx}  {flag}")
    if pct >= 0.75:
        pass_count += 1
    total_count += 1

print(f"\n总达标率: {pass_count}/{total_count}  ({pass_count/total_count*100:.0f}%)")
