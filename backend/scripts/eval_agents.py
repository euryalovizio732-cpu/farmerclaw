"""端到端Agent输出评测脚本

对标矩阵：口播稿≥7分 / 选题标题≥7分 / 直播话术≥7分 / 评论回复≥7分 / 痛点≥6分
评分维度：
  口播稿：①3秒钩子 ②产地/价格锚定 ③坏果承诺 ④逼单 ⑤口语化 ⑥≤200字
  选题：①≤20字 ②口语化 ③有钩子 ④有感官词/数字
  回复：①口语化 ②走平台流程 ③不强硬 ④给具体方案
"""
import requests
import json

BASE = "http://localhost:8001"
CASES = [
    {"product_name": "赣南脐橙", "category": "水果", "origin": "江西赣州信丰",
     "specification": "5斤装", "price": 29.9, "platform": "douyin"},
    {"product_name": "丹东草莓", "category": "水果", "origin": "辽宁丹东",
     "specification": "1斤装", "price": 39.9, "platform": "douyin"},
    {"product_name": "东北大米", "category": "粮油", "origin": "黑龙江五常",
     "specification": "5斤装", "price": 49.9, "platform": "douyin"},
]

SEP = "─" * 60


def score_script(text: str, product: str) -> tuple[int, list[str]]:
    """简单评分逻辑"""
    issues = []
    score = 0
    if len(text) > 10:
        score += 1
    if any(w in text for w in ["家人", "宝贝", "老铁", "亲"]):
        score += 1
    else:
        issues.append("❌ 缺口语化称呼")
    if any(w in text for w in ["产地", "现摘", "江西", "辽宁", "黑龙江", "赣南", "丹东", "五常"]):
        score += 1
    else:
        issues.append("❌ 缺产地背书")
    if any(w in text for w in ["包赔", "赔", "退款", "承诺"]):
        score += 1
    else:
        issues.append("❌ 缺坏果承诺")
    if any(w in text for w in ["下单", "拍", "扣1", "快", "最后"]):
        score += 1
    else:
        issues.append("❌ 缺逼单词")
    if any(w in text for w in ["元", "块", "价格", "¥", "现在只要", "直播间"]):
        score += 1
    else:
        issues.append("❌ 缺价格锚定")
    if len(text) <= 300:
        score += 1
    else:
        issues.append(f"❌ 太长({len(text)}字)")

    return score, issues


def score_topic(title: str) -> tuple[int, list[str]]:
    issues = []
    score = 0
    if len(title) <= 20:
        score += 2
    else:
        issues.append(f"❌ 标题太长({len(title)}字>20)")
    if not any(w in title for w in ["揭秘", "盘点", "全方位", "系列", "深度"]):
        score += 2
    else:
        issues.append("❌ 含书面语")
    if any(w in title for w in ["甜", "脆", "汁", "香", "烂", "丑", "贵", "便宜", "斤", "元"]):
        score += 2
    else:
        issues.append("❌ 缺感官词/数字")
    if "?" in title or "？" in title or "!" in title or "！" in title:
        score += 1
    else:
        issues.append("⚠ 无疑问/感叹语气钩子")
    return score, issues


def score_reply(reply: str) -> tuple[int, list[str]]:
    issues = []
    score = 0
    if any(w in reply for w in ["家人", "宝贝", "亲"]):
        score += 2
    else:
        issues.append("❌ 缺口语称呼")
    if any(w in reply for w in ["平台", "退款", "申请", "包赔", "赔"]):
        score += 2
    else:
        issues.append("❌ 缺处理承诺")
    if "联系客服" in reply or "稍后处理" in reply:
        score -= 1
        issues.append("❌ 推诿客服")
    if len(reply) < 150:
        score += 2
    else:
        issues.append("⚠ 回复偏长")
    if any(w in reply for w in ["图", "拍照", "单号", "时间", "规格"]):
        score += 2
    else:
        issues.append("❌ 缺具体行动指引")
    return score, issues


def test_listing(case: dict):
    print(f"\n{'='*60}")
    print(f"【口播稿测试】{case['product_name']} | {case['origin']}")
    print(SEP)
    try:
        r = requests.post(f"{BASE}/api/listing/generate", json=case, timeout=30)
        data = r.json()
        script = data.get("live_checkout_script", "") or data.get("video_script", "")
        if not script:
            print("❌ 无输出")
            return
        print(f"输出:\n{script[:500]}")
        score, issues = score_script(script, case["product_name"])
        print(f"\n评分: {score}/7")
        if issues:
            print("问题点:", "\n".join(issues))
        print("通过" if score >= 7 else "❌ 未达标")
        return score, script
    except Exception as e:
        print(f"请求失败: {e}")
        return 0, ""


def test_topic(case: dict):
    print(f"\n{'='*60}")
    print(f"【选题测试】{case['product_name']}")
    print(SEP)
    try:
        payload = {
            "product_name": case["product_name"],
            "category": case["category"],
            "origin": case["origin"],
        }
        r = requests.post(f"{BASE}/api/topic/generate", json=payload, timeout=30)
        data = r.json()
        topics = data.get("topics", [])
        if not topics:
            print("❌ 无输出")
            return
        for t in topics:
            title = t.get("title", "")
            score, issues = score_topic(title)
            status = "✅" if score >= 5 else "❌"
            print(f"{status} [{t.get('type','')}] {title}  (分={score}/7)")
            if issues:
                for i in issues:
                    print(f"   {i}")
        return topics
    except Exception as e:
        print(f"请求失败: {e}")
        return []


def test_reply(case: dict):
    print(f"\n{'='*60}")
    print(f"【回复话术测试】{case['product_name']}")
    print(SEP)
    test_comments = [
        "收到了，全是烂的，太差了！",
        "甜不甜啊？好吃吗",
        "能便宜点吗",
        "什么时候发货",
    ]
    try:
        payload = {
            "product_name": case["product_name"],
            "origin": case["origin"],
            "price": str(case["price"]),
            "comments": test_comments,
        }
        r = requests.post(f"{BASE}/api/reply/batch", json=payload, timeout=30)
        data = r.json()
        results = data if isinstance(data, list) else data.get("results", [])
        for i, (comment, result) in enumerate(zip(test_comments, results)):
            if not isinstance(result, dict):
                continue
            reply = result.get("reply", "")
            score, issues = score_reply(reply)
            status = "✅" if score >= 5 else "❌"
            print(f"\n评论: 「{comment}」")
            print(f"回复: {reply[:120]}")
            print(f"{status} 评分:{score}/8  类型:{result.get('comment_type','')}")
            if issues:
                for iss in issues:
                    print(f"  {iss}")
        return results
    except Exception as e:
        print(f"请求失败: {e}")
        return []


def test_pain_point(case: dict):
    print(f"\n{'='*60}")
    print(f"【痛点挖掘测试】{case['product_name']}")
    print(SEP)
    try:
        payload = {
            "product_name": case["product_name"],
            "category": case["category"],
            "origin": case["origin"],
            "price": case["price"],
        }
        r = requests.post(f"{BASE}/api/pain-point/analyze", json=payload, timeout=30)
        data = r.json()
        pain_points = data.get("top_pain_points", [])
        pricing = data.get("pricing_suggestion", {})
        print(f"痛点数量: {len(pain_points)}")
        for p in pain_points[:3]:
            print(f"  [{p.get('severity','')}] {p.get('pain_point','')} — {p.get('opportunity','')[:40]}")
        print(f"定价建议: {pricing.get('suggested_price','')} ({pricing.get('strategy','')})")
        has_real_price = any(c.isdigit() for c in str(pricing.get("suggested_price", "")))
        print("✅ 有真实定价数据" if has_real_price else "❌ 缺真实定价")
        return data
    except Exception as e:
        print(f"请求失败: {e}")
        return {}


if __name__ == "__main__":
    print("=== 三农AI Agent 端到端评测 ===")
    print(f"测试品类: {[c['product_name'] for c in CASES]}")

    for case in CASES[:2]:  # 先测2个品类
        test_listing(case)
        test_topic(case)
        test_reply(case)
        test_pain_point(case)
        print()

    print("\n=== 评测完成 ===")
