"""质量基准测试：用新品类(攀枝花芒果)逐环节生成 → 输出结果供与真实案例比对"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.topic_agent import topic_agent, TopicRequest
from app.services.listing_agent import listing_agent, ListingRequest
from app.services.reply_agent import reply_agent, ReplyRequest, BatchReplyRequest
from app.services.pain_point_agent import pain_point_agent, PainPointRequest, PainPointReport
from app.services.live_review_agent import live_review_agent, LiveReviewRequest
from app.services.knowledge_base import kb

PRODUCT = "攀枝花芒果"
CATEGORY = "水果"
ORIGIN = "四川攀枝花"
SPEC = "5斤装"
PRICE = "29.9元"

results = {}

def banner(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# ── 0. 知识库路由检查 ────────────────────────────
banner("环节0: 知识库路由检查")
canon = kb.resolve_best_category(PRODUCT, CATEGORY)
insights = kb.get_category_insights(canon)
pricing = kb.get_market_pricing(canon)
core_words = kb.get_category_core_words(canon)
fact_block = kb.build_fact_block(canon)
print(f"  canonical: {canon}")
print(f"  产地: {insights.get('origin', '❌ 无')}")
print(f"  特征: {insights.get('product_traits', [])}")
print(f"  电商价: {pricing.get('ecom_range', '❌ 无') if pricing else '❌ 无'}")
print(f"  核心词: {core_words[:4]}")
print(f"  fact_block行数: {len(fact_block.strip().splitlines())}")
results["knowledge_base"] = {
    "canonical": canon,
    "origin": insights.get("origin", ""),
    "traits": insights.get("product_traits", []),
    "pricing": pricing.get("ecom_range", "") if pricing else "",
    "core_words": core_words[:4],
}

# ── 1. 选题生成 ────────────────────────────
banner("环节1: 选题生成 (TopicAgent)")
t0 = time.time()
topic_result = topic_agent.generate(TopicRequest(
    product_name=PRODUCT,
    category=CATEGORY,
    origin=ORIGIN,
))
t1 = time.time()
print(f"  耗时: {t1-t0:.1f}s")
print(f"  今日建议: {topic_result.today_tip}")
topics_out = []
for i, t in enumerate(topic_result.topics, 1):
    print(f"\n  选题{i}: {t.get('title', '?')}")
    print(f"    类型: {t.get('type', '?')}")
    print(f"    核心冲突: {t.get('core_conflict', '?')}")
    print(f"    拍摄角度: {t.get('shooting_angle', '?')}")
    kw = t.get('oral_keywords', [])
    if kw:
        print(f"    口播关键词: {kw}")
    topics_out.append(t)
results["topics"] = topics_out

# ── 2. 口播稿生成 ────────────────────────────
banner("环节2: 口播稿生成 (ListingAgent)")
t0 = time.time()
listing_result = listing_agent.generate(ListingRequest(
    product_name=PRODUCT,
    category=CATEGORY,
    origin=ORIGIN,
    specification=SPEC,
    price=PRICE,
    platform="douyin",
))
t1 = time.time()
print(f"  耗时: {t1-t0:.1f}s")
vs = listing_result.video_script or {}
full_script = vs.get("full_script", "") if isinstance(vs, dict) else str(vs)
print(f"  标题: {listing_result.title}")
print(f"  口播稿全文 ({len(full_script)}字):")
print(f"  {full_script}")
print(f"\n  钩子(0-3s): {vs.get('hook_0_3s', '')}")
print(f"  CTA(25-30s): {vs.get('cta_25_30s', '')}")
print(f"  标签: {listing_result.hashtags}")
results["script"] = {
    "title": listing_result.title,
    "full_script": full_script,
    "length": len(full_script),
}

# ── 3. 评论回复 ────────────────────────────
banner("环节3: 评论回复 (ReplyAgent)")
test_comments = [
    "收到了全是烂的，芒果都黑了！",
    "好吃吗？甜不甜",
    "能便宜点吗，5斤太贵了",
    "什么时候发货啊",
    "太好吃了，汁水很多，下次还买！",
]
t0 = time.time()
batch_result = reply_agent.batch_generate(BatchReplyRequest(
    product_name=PRODUCT,
    origin=ORIGIN,
    price=PRICE,
    comments=test_comments,
))
t1 = time.time()
print(f"  耗时: {t1-t0:.1f}s")
replies_out = []
for comment, rep in zip(test_comments, batch_result):
    reply_text = rep.reply if hasattr(rep, 'reply') else rep.get('reply', '') if isinstance(rep, dict) else str(rep)
    ctype = rep.comment_type if hasattr(rep, 'comment_type') else rep.get('comment_type', '') if isinstance(rep, dict) else ''
    print(f"\n  [{ctype}] 「{comment}」")
    print(f"      → {reply_text}")
    replies_out.append({"comment": comment, "type": ctype, "reply": reply_text})
results["replies"] = replies_out

# ── 4. 痛点分析 ────────────────────────────
banner("环节4: 痛点分析 (PainPointAgent)")
t0 = time.time()
pp_result = pain_point_agent.analyze(PainPointRequest(
    category=CATEGORY,
    product_name=PRODUCT,
    platform="douyin",
))
t1 = time.time()
print(f"  耗时: {t1-t0:.1f}s")
pain_points = pp_result.top_pain_points or []
print(f"  痛点数: {len(pain_points)}")
for p in pain_points[:5]:
    if isinstance(p, dict):
        print(f"  [{p.get('frequency', p.get('severity', ''))}] {p.get('pain_point', '')}")
        opp = p.get("opportunity", "")
        if opp:
            print(f"       机会: {str(opp)[:60]}")
pricing_sug = pp_result.pricing_suggestion or {}
if isinstance(pricing_sug, dict):
    print(f"  定价建议: {pricing_sug.get('suggested_price_range', pricing_sug.get('suggested_price', ''))}")
kw_opp = pp_result.keyword_opportunities or []
if kw_opp:
    print(f"  关键词机会: {kw_opp[:5]}")
results["pain_points"] = {
    "count": len(pain_points),
    "top3": [p.get("pain_point", "") for p in pain_points[:3] if isinstance(p, dict)],
}

# ── 5. 直播话术 ────────────────────────────
banner("环节5: 直播话术复盘 (LiveReviewAgent)")
t0 = time.time()
live_result = live_review_agent.analyze(LiveReviewRequest(
    category=CATEGORY,
    product_name=PRODUCT,
    duration=120,
    peak_viewers=350,
    avg_viewers=180,
    comments=210,
    likes=1500,
    orders=85,
    gmv=2541.5,
    refund_rate=3.2,
    script_notes="家人们好，今天给大家带来我们攀枝花的芒果，凯特芒，个头大，果肉厚，纤维少。现在5斤装只要29.9，比超市便宜一半。攀枝花日照3000小时，昼夜温差大，这芒果甜度能到15度以上。坏果包赔，顺丰冷链发货。需要的赶紧下单！",
))
t1 = time.time()
print(f"  耗时: {t1-t0:.1f}s")
print(f"  总分: {live_result.overall_score}")
print(f"  评分理由: {live_result.score_reason}")
if live_result.highlight:
    print(f"  亮点: {live_result.highlight}")
if live_result.problems:
    print(f"  问题:")
    for p in live_result.problems[:3]:
        print(f"    - {p}")
if live_result.improvements:
    print(f"  改进建议:")
    for s in live_result.improvements[:3]:
        print(f"    - {s}")
if live_result.next_session_plan:
    print(f"  下场计划: {live_result.next_session_plan}")
results["live_review"] = {
    "score": live_result.overall_score,
    "score_reason": live_result.score_reason,
    "highlight": live_result.highlight or "",
    "problems_count": len(live_result.problems or []),
    "improvements_count": len(live_result.improvements or []),
}

# ── 输出JSON供后续比对 ────────────────────────────
banner("JSON输出（供比对）")
output_path = os.path.join(os.path.dirname(__file__), "benchmark_output.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"  已保存到: {output_path}")
print("\n✅ 5个环节全部完成！")
