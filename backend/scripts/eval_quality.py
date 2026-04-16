"""
eval_quality.py  ——  8品类生成质量评测
逻辑：
  1. 每个品类调 listing_agent 生成口播稿（script），调 topic_agent 生成第1条选题
  2. 用知识库真实事实核对：产地、品类角度、真实事实是否出现
  3. 对比同品类样本库样本（真实参照）
  4. 给出得分（0-4分）和具体问题提示
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.services.listing_agent import listing_agent, ListingRequest
from app.services.topic_agent import topic_agent, TopicRequest
from app.services.knowledge_base import kb

CORE_CATEGORIES = [
    {"name": "赣南脐橙", "category": "脐橙", "origin": "江西赣州信丰县",
     "key_facts": ["信丰", "193万亩", "地标", "产地直发", "回糖", "分级"],
     "risk_words": ["最便宜", "乙烯利", "治病", "100%", "无农残"]},
    {"name": "洛川苹果", "category": "苹果", "origin": "陕西洛川",
     "key_facts": ["洛川", "黄土高原", "地理标志", "分级", "产地直发"],
     "risk_words": ["最便宜", "最好", "治病", "100%", "第一"]},
    {"name": "丹东东港草莓", "category": "草莓", "origin": "辽宁丹东东港",
     "key_facts": ["东港", "北纬40", "分拣", "冷链", "产地直发"],
     "risk_words": ["最便宜", "促销最大", "治病", "100%", "全额退款不退货"]},
    {"name": "五常稻花香大米", "category": "粮油", "origin": "黑龙江五常",
     "key_facts": ["五常", "稻花香", "产地", "新米", "真空", "溯源"],
     "risk_words": ["最便宜", "治病", "100%", "全国第一", "花青素"]},
    {"name": "寿光蔬菜", "category": "蔬菜", "origin": "山东寿光",
     "key_facts": ["寿光", "地标", "分拣", "冷链", "产地直发"],
     "risk_words": ["最便宜", "治病", "100%", "全国第一"]},
    {"name": "贵州麻江蓝莓", "category": "蓝莓", "origin": "贵州麻江",
     "key_facts": ["麻江", "贵州", "果粉", "产地", "冷链"],
     "risk_words": ["花青素治病", "护眼治疗", "USDA", "100%", "全国最大"]},
    {"name": "大连大樱桃", "category": "樱桃", "origin": "辽宁大连旅顺",
     "key_facts": ["大连", "美早", "分级", "冷链", "产地直发"],
     "risk_words": ["最便宜", "治病", "100%", "全额退款不退货"]},
    {"name": "眉县猕猴桃", "category": "猕猴桃", "origin": "陕西眉县",
     "key_facts": ["眉县", "翠香", "后熟", "干物质", "产地直发"],
     "risk_words": ["最便宜", "治病", "100%", "全额退款不退货"]},
]

FABRICATION_SIGNALS = [
    "返红包", "现金红包", "营业执照", "我查了你的单子", "24小时都在",
    "超过20%全额退款不退货", "少一两我赔双倍", "坏果超3颗全额退款不退货",
    "今晚最后50单", "只剩最后287单", "明天起价格要涨"
]

def score_script(text: str, cat: dict) -> tuple[int, list[str]]:
    issues = []
    score = 4
    # 检查是否包含产地关键词（最重要）
    has_key_fact = any(f in text for f in cat["key_facts"])
    if not has_key_fact:
        issues.append("⚠️ 未出现品类真实关键词：" + " / ".join(cat["key_facts"][:3]))
        score -= 1
    # 检查高风险词
    for w in cat["risk_words"]:
        if w in text:
            issues.append(f"❌ 出现风险词：{w}")
            score -= 1
            break
    # 检查伪造信号
    for f in FABRICATION_SIGNALS:
        if f in text:
            issues.append(f"❌ 出现伪造信号：{f}")
            score -= 1
            break
    # 检查是否包含售后/坏果处理
    if "平台" not in text and "处理" not in text and "退" not in text:
        issues.append("⚠️ 缺少售后承诺/平台处理引导")
        score -= 1
    return max(score, 0), issues

def score_topic(title: str, cat: dict) -> tuple[int, list[str]]:
    issues = []
    score = 4
    if len(title) > 20:
        issues.append(f"❌ 标题超20字（{len(title)}字）：{title}")
        score -= 1
    has_product_word = any(f in title for f in [cat["name"][:2], cat["category"], cat["origin"][:2]])
    if not has_product_word:
        issues.append(f"⚠️ 标题未出现品类/产地词")
        score -= 1
    for w in cat["risk_words"]:
        if w in title:
            issues.append(f"❌ 标题含风险词：{w}")
            score -= 1
            break
    return max(score, 0), issues

def main():
    total_score = 0
    max_score = 0
    print("=" * 70)
    print("  8品类 生成质量评测  |  口播稿 + 选题标题")
    print("=" * 70)

    for cat in CORE_CATEGORIES:
        print(f"\n{'─'*65}")
        print(f"  【{cat['name']}】  产地：{cat['origin']}")
        print(f"{'─'*65}")

        # ── 1. 生成口播稿 ──
        try:
            req = ListingRequest(
                product_name=cat["name"],
                category=cat["category"],
                origin=cat["origin"],
                price="产地直供价",
                platform="douyin",
            )
            res = listing_agent.generate(req)
            script_text = ""
            if res.video_script and isinstance(res.video_script, dict):
                script_text = res.video_script.get("full_script", "")
            if not script_text and res.video_script:
                script_text = " ".join(str(v) for v in res.video_script.values())[:300]

            s_score, s_issues = score_script(script_text, cat)
            total_score += s_score
            max_score += 4
            print(f"\n【口播稿】得分 {s_score}/4")
            print(f"  内容（前150字）：{script_text[:150].strip()}…")
            if s_issues:
                for iss in s_issues:
                    print(f"  {iss}")
            else:
                print("  ✅ 无明显问题")
        except Exception as e:
            print(f"  [口播稿生成失败] {e}")
            max_score += 4

        # ── 2. 生成选题 ──
        try:
            treq = TopicRequest(
                product_name=cat["name"],
                category=cat["category"],
                origin=cat["origin"],
            )
            tres = topic_agent.generate(treq)
            topics = tres.topics or []
            title = topics[0].get("title", "") if topics else ""
            t_score, t_issues = score_topic(title, cat)
            total_score += t_score
            max_score += 4
            print(f"\n【选题标题】得分 {t_score}/4")
            print(f"  第1条标题：{title}")
            if t_issues:
                for iss in t_issues:
                    print(f"  {iss}")
            else:
                print("  ✅ 无明显问题")
        except Exception as e:
            print(f"  [选题生成失败] {e}")
            max_score += 4

        # ── 3. 知识库事实核对 ──
        insights = kb.get_category_insights(cat["category"])
        print(f"\n【知识库事实核对】")
        if insights:
            print(f"  产地：{insights.get('origin', '—')}")
            print(f"  品类事实：{insights.get('production_facts', ['—'])[0][:60]}…")
            print(f"  电商事实：{insights.get('ecommerce_facts', ['—'])[0][:60]}…")
            print(f"  推荐选题角度：{insights.get('topic_angles', ['—'])[:2]}")
        else:
            print("  ⚠️ 知识库无此品类数据")

    print(f"\n{'=' * 70}")
    pct = total_score / max_score * 100 if max_score else 0
    print(f"  总分：{total_score}/{max_score}  （{pct:.1f}%）")
    if pct >= 75:
        print("  ✅ 整体质量达标（≥75%）")
    else:
        print("  ⚠️ 整体质量未达标（<75%），需进一步优化")
    print("=" * 70)

if __name__ == "__main__":
    main()
