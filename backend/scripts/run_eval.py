"""运行完整评测，输出直接可读结果"""
import requests, json

BASE = "http://localhost:8001"

def divider(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

def section(title):
    print(f"\n--- {title} ---")


divider("品类1: 赣南脐橙")

# 口播稿
r = requests.post(f"{BASE}/api/listing/generate", json={
    "product_name": "赣南脐橙", "category": "水果",
    "origin": "江西赣州信丰", "specification": "5斤装",
    "price": "29.9元/5斤", "platform": "douyin"
}, timeout=60)
d = r.json()["data"]

vs_raw = d.get("video_script", "")
ls_raw = d.get("live_script", "")
vs = vs_raw.get("full_script", "") if isinstance(vs_raw, dict) else str(vs_raw)
title = d.get("title", "")

section("标题")
print(title)

section(f"视频口播 ({len(vs)}字)")
print(vs)
# 评分
checks = {
    "家人/宝贝": any(w in vs for w in ["家人", "宝贝", "老铁"]),
    "产地": any(w in vs for w in ["赣南", "信丰", "江西", "产地", "现摘"]),
    "承诺/包赔": any(w in vs for w in ["包赔", "赔", "退款", "承诺"]),
    "逼单": any(w in vs for w in ["下单", "拍", "快", "最后", "限量", "只剩"]),
    "价格锚定": any(w in vs for w in ["元", "块", "只要", "优惠"]),
    "长度合理(≤350)": len(vs) <= 350,
}
sc = sum(checks.values())
print(f"\n铁律评分: {sc}/6  {'✅达标' if sc >= 5 else '❌未达标'}")
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'} {k}")

section("直播话术")
if isinstance(ls_raw, dict):
    for k, v in ls_raw.items():
        print(f"[{k}]: {v}")
else:
    print(str(ls_raw)[:400])

# 评分直播话术
ls_text = " ".join(str(v) for v in ls_raw.values()) if isinstance(ls_raw, dict) else str(ls_raw)
checks2 = {
    "口语称呼": any(w in ls_text for w in ["家人", "宝贝", "亲"]),
    "产地/源头": any(w in ls_text for w in ["产地", "赣南", "信丰", "果园"]),
    "承诺保障": any(w in ls_text for w in ["包赔", "赔", "退款", "坏果"]),
    "逼单/紧迫": any(w in ls_text for w in ["最后", "只剩", "手快", "限量", "马上"]),
    "互动指令": any(w in ls_text for w in ["扣", "评论", "关注", "点赞"]),
    "价格": any(w in ls_text for w in ["元", "块", "只要", "优惠"]),
}
sc2 = sum(checks2.values())
print(f"\n直播铁律评分: {sc2}/6  {'✅达标' if sc2 >= 5 else '❌未达标'}")
for k, v in checks2.items():
    print(f"  {'✅' if v else '❌'} {k}")


divider("评论回复测试")
test_comments = [
    "收到了全是烂的，太差劲了！",
    "甜不甜啊？好吃吗",
    "能不能便宜点，贵死了",
    "什么时候发货啊，等了好几天",
    "收到了，很甜！！！",
]
r2 = requests.post(f"{BASE}/api/reply/batch", json={
    "product_name": "赣南脐橙",
    "origin": "江西赣州信丰",
    "price": "29.9元/5斤",
    "comments": test_comments
}, timeout=30)
rdata = r2.json()
replies = rdata if isinstance(rdata, list) else rdata.get("data", [])

for comment, rep in zip(test_comments, replies):
    if not isinstance(rep, dict):
        continue
    reply = rep.get("reply", "")
    ctype = rep.get("comment_type", "")
    urgency = rep.get("urgency", "")
    action = rep.get("follow_up_action", "")

    r_checks = {
        "口语": any(w in reply for w in ["家人", "宝贝", "亲"]),
        "平台流程/承诺": any(w in reply for w in ["平台", "退款", "申请", "包赔", "承诺", "赔"]),
        "无推诿": "联系客服" not in reply,
        "具体行动": any(w in reply for w in ["图", "拍照", "单号", "规格", "申请", "平台"]),
    }
    rsc = sum(r_checks.values())
    print(f"\n评论: 「{comment}」")
    print(f"类型:{ctype} 紧迫度:{urgency}")
    print(f"回复: {reply}")
    print(f"短回复: {rep.get('reply_short','')}")
    print(f"行动: {action}")
    issues = [k for k,v in r_checks.items() if not v]
    print(f"评分:{rsc}/4  {'✅' if rsc>=3 else '❌'}" + (f"  问题:{issues}" if issues else ""))


divider("痛点分析: 赣南脐橙")
r3 = requests.post(f"{BASE}/api/pain-point/analyze", json={
    "product_name": "赣南脐橙", "category": "水果",
    "origin": "江西赣州信丰", "price": 29.9
}, timeout=30)
ppd = r3.json().get("data", r3.json())
top_pp = ppd.get("top_pain_points", [])
pricing = ppd.get("pricing_suggestion", {})
diff = ppd.get("differentiation_opportunities", [])

print(f"痛点数: {len(top_pp)}")
for p in top_pp[:5]:
    if isinstance(p, dict):
        sev = p.get("severity", "")
        pp_text = p.get("pain_point", "")
        opp = p.get("opportunity", "")
        print(f"  [{sev}] {pp_text}")
        print(f"         机会: {opp[:60]}")

print(f"\n定价建议: {pricing.get('suggested_price', '无')}  ({pricing.get('strategy', '')})")
print(f"理由: {pricing.get('reason', '')[:80]}")

print("\n差异化机会:")
for d_item in diff[:3]:
    if isinstance(d_item, str):
        print(f"  - {d_item[:60]}")
    elif isinstance(d_item, dict):
        print(f"  - {str(d_item)[:60]}")

print(f"\n{'='*55}")
print("评测完成")
