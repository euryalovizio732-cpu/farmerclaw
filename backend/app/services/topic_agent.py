"""抖音三农选题 Agent

功能：根据产品信息 + 当前节气/日期，生成 3 条差异化抖音选题方向
每条选题包含：选题标题、封面第一帧建议、拍摄角度、核心矛盾、预估完播率
"""

from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

from app.services.llm_service import llm_service
from app.services.knowledge_base import kb
from app.services.sample_library import get_few_shot_samples, format_few_shot_block
from app.services.compliance_engine import compliance_engine


TOPIC_SYSTEM_PROMPT = """你是一位抖音三农内容爆款策划专家，精通农产品短视频选题方法论。

【真实市场数据警示 — 来自48054条消费舆情调研】
农产品直播电商消费者最大痛点（2023年N=48054真实舆情数据）：
- 虚假宣传占比52.48%（最大问题）：货不对板、假冒产地、摆拍助农
- 质量问题占比22.77%：运输损坏、以次充好、缺斤短两
- 价格诱导占比11.88%：普通品冒充特产

→ 选题核心策略：【主动展示真实性】才能形成反差，获得用户信任
→ 选题禁区：不做摆拍、不夸大、不假冒产地

【三农爆款选题7大模式（来自真实爆款归纳）】
1. 反差钩子：丑但超甜/冷门产地出好货（例：汉源苹果核心记忆点：「丑，但脆甜多汁」）
2. 知识科普：怎么选/为什么贵/产地有什么不同
3. 产地实录：实时直播产地/采摘全过程（消费者最信任「所见即所得」）
4. 情感故事：一个农民的故事/土地情怀（原汁原味、朴实才是核心）
5. 悬念揭秘：我本来不打算卖/告诉你个秘密
6. 对比测评：产地vs超市/贵的vs便宜的（附真实数据）
7. 痛点解决：买过烂货?/怎么辨别真假/教你避坑

【选题标题铁律（必须全部遵守）】
① 标题≤20字，超过20字用户会划走
② 必须口语化，禁止书面语（不能有「揭秘」「盘点」「全方位」「系列」等词）
③ 有数字更好（3招/5斤/100%/第一次）
④ 有感官词更好（爆汁/脆甜/糯叽叽/嘎嘣脆/流心）
⑤ 有产地/品种具体感（「赣南脐橙」比「橙子」好，「冰糖心」比「苹果」好）
⑥ 主角是产品和农民，不是主播人设

【真实数据铁律】
- 只能使用输入里的真实知识库事实、样本和公开价格带，不能编造亩数、销量、库存、认证、物流数据
- 如果缺少具体事实，就老老实实写产地实拍、分级、时令、售后，不要硬补数字

请严格按照JSON格式返回，生成3条选题，每条包含完整信息。"""


TOPIC_USER_PROMPT_TEMPLATE = """请为以下农产品生成3条抖音爆款选题：

产品信息：
- 产品名称：{product_name}
- 品类：{category}
- 产地：{origin}
- 核心卖点：{core_features}
- 当前月份：{month}月（{season}，{solar_term}）
- 当季营销角度：{season_angle}

真实知识库事实：
{fact_block}

高频种草词：
- {core_words}

参考选题钩子模式：
{hook_patterns}

请生成JSON格式：
{{
  "today_tip": "今天适合推的方向（结合节气/时令给出一句话建议，30字内）",
  "topics": [
    {{
      "topic_id": 1,
      "type": "选题类型（反差/知识/探访/情感/悬念/对比/痛点）",
      "title": "选题标题（即视频标题，≤20字，有强钩子，必须口语化，有感官词/数字/产地）",
      "first_frame": "封面第一帧建议（描述画面构图+文字标注，40字内）",
      "shooting_angle": "拍摄角度建议（怎么拍，拍什么场景，20字内）",
      "core_conflict": "核心矛盾/反差点（这条视频的爆点在哪，20字内）",
      "estimated_completion_rate": "预估完播率（高/中，及原因）",
      "oral_keywords": ["口播时要说的关键词1", "关键词2", "关键词3"]
    }},
    {{
      "topic_id": 2,
      ...
    }},
    {{
      "topic_id": 3,
      ...
    }}
  ],
  "hashtags": ["#三农", "#助农", "#产地直发", "#相关热词1", "#相关热词2"]
}}"""


@dataclass
class TopicRequest:
    product_name: str
    category: str
    origin: str = ""
    core_features: str = ""


@dataclass
class TopicResult:
    today_tip: str
    topics: list[dict] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    season_info: dict = field(default_factory=dict)


class TopicAgent:
    """抖音三农选题 Agent"""

    def generate(self, request: TopicRequest) -> TopicResult:
        logger.info("TopicAgent: 开始生成选题 product={}", request.product_name)

        # 注入节气知识库
        season_info = kb.get_today_season()
        hook_patterns = kb.get_hook_patterns()
        canonical_category = kb.resolve_best_category(request.product_name, request.category)
        fact_block = kb.build_fact_block(canonical_category or request.product_name)
        core_words = "、".join(kb.get_category_core_words(canonical_category or request.category)[:8])

        hook_str = "\n".join(
            f"- [{p['type']}] {p['template']}（{p['angle']}）"
            for p in hook_patterns[:5]
        )

        # Few-shot 注入：获取真实选题样本
        sample_key = canonical_category or request.category
        samples = get_few_shot_samples(sample_key, sample_type="topic", count=3)
        if len(samples) < 3 and request.product_name != sample_key:
            extra = get_few_shot_samples(request.product_name, sample_type="topic", count=3 - len(samples))
            samples.extend(extra)
        few_shot_block = format_few_shot_block(samples, sample_type="topic")
        if few_shot_block:
            system_prompt = TOPIC_SYSTEM_PROMPT + "\n\n" + few_shot_block
            logger.info("TopicAgent: 注入{}条真实选题样本（品类:{}）", len(samples), sample_key)
        else:
            system_prompt = TOPIC_SYSTEM_PROMPT

        user_prompt = TOPIC_USER_PROMPT_TEMPLATE.format(
            product_name=request.product_name,
            category=canonical_category or request.category,
            origin=request.origin or kb.get_category_insights(canonical_category).get("origin", "产地"),
            core_features=request.core_features or f"新鲜{request.category}，产地直发",
            month=datetime.now().month,
            season=season_info.get("season", ""),
            solar_term=season_info.get("solar_term", ""),
            season_angle=season_info.get("angle", ""),
            hook_patterns=hook_str,
            fact_block=fact_block or "- 暂无额外公开事实，优先拍产地实景和发货过程",
            core_words=core_words or "产地直发、分级发货、坏果包赔",
        )

        try:
            raw = llm_service.chat_json(system_prompt, user_prompt)
        except Exception as exc:
            logger.error("TopicAgent LLM 失败: {}", exc)
            raw = self._fallback(request, season_info)

        # 合规检查 + 强制20字截断
        for topic in raw.get("topics", []):
            title = topic.get("title", "")
            if not title:
                continue
            issues = compliance_engine.check(title, "标题")
            if issues:
                fixed = next((iss.auto_fix for iss in issues if iss.auto_fix), "")
                if fixed:
                    topic["title"] = fixed
                    title = fixed
                    topic["compliance_fixed"] = True
            # 标题超20字：截断到最近一个标点
            if len(title) > 20:
                cut = title[:20]
                for punct in "！？!?，、":
                    last = cut.rfind(punct)
                    if last >= 10:
                        cut = cut[: last + 1]
                        break
                logger.warning("标题超20字，已截断: {} → {}", title, cut)
                topic["title"] = cut
                topic["title_truncated"] = True

        return TopicResult(
            today_tip=raw.get("today_tip", f"今天适合推{request.product_name}，结合{season_info.get('solar_term','')}时令做内容"),
            topics=raw.get("topics", []),
            hashtags=raw.get("hashtags", ["#三农", "#助农", "#产地直发"]),
            season_info=season_info,
        )

    def _fallback(self, request: TopicRequest, season_info: dict) -> dict:
        """Fallback：优先取样本库真实选题，无匹配则用口语化模板"""
        from app.services.sample_library import get_few_shot_samples
        product = request.product_name
        canonical_category = kb.resolve_best_category(product, request.category)
        insights = kb.get_category_insights(canonical_category)
        core_words = kb.get_category_core_words(canonical_category or request.category)
        origin = request.origin or insights.get("origin", "产地")
        solar_term = season_info.get("solar_term", "")
        season = season_info.get("season", "当季")

        # 优先从样本库取真实选题标题
        real_topics = get_few_shot_samples(canonical_category or product, "topic", count=3)
        if not real_topics:
            real_topics = get_few_shot_samples("通用", "topic", count=3)

        topics = []
        # 3个真实数据钩子模板（口语化，无书面语）
        topic_angles = insights.get("topic_angles", [])
        fallback_titles = [
            (topic_angles[0] if len(topic_angles) > 0 else f"{product}丑但爆汁！产地教你挑", "知识反问"),
            (topic_angles[1] if len(topic_angles) > 1 else f"超市{product}和产地的差在哪？", "对比钩子"),
            (topic_angles[2] if len(topic_angles) > 2 else f"{origin}{product}今天刚摘的！", "产地实录"),
        ]
        for i, sample in enumerate(real_topics[:3]):
            title = sample.get("title", fallback_titles[i][0])
            hook = sample.get("hook_type", fallback_titles[i][1])
            # 标题超20字截断
            if len(title) > 20:
                title = title[:20]
            topics.append({
                "topic_id": i + 1,
                "type": hook,
                "title": title,
                "first_frame": f"{origin}{product}产地实景特写，展示{['剖开瞬间', '新鲜采摘', '糖度测试'][i]}",
                "shooting_angle": ["特写剖开，外观vs内部对比", "田间地头产地实拍", "糖度计测试展示"][i],
                "core_conflict": f"真实产地直发vs超市陈货，价格差、新鲜度差",
                "estimated_completion_rate": "高",
                "oral_keywords": [origin, product] + (core_words[:2] or ["产地直发", "坏果包赔"]),
            })

        # 不足3条时补上模板
        while len(topics) < 3:
            i = len(topics)
            topics.append({
                "topic_id": i + 1,
                "type": fallback_titles[i][1],
                "title": fallback_titles[i][0],
                "first_frame": f"{origin}{product}实景，配文：产地直发，今天摘的",
                "shooting_angle": "田间地头，展示采摘",
                "core_conflict": "产地直发vs超市陈货",
                "estimated_completion_rate": "中",
                "oral_keywords": [origin, product, "今日采摘", "现摘现发"],
            })

        return {
            "today_tip": f"{solar_term or season}时令，优先讲{(topic_angles[0] if topic_angles else product)}，突出产地实拍和真实分级",
            "topics": topics,
            "hashtags": ["#三农", "#助农", "#产地直发", f"#{product}", f"#{origin}{product}"],
        }


topic_agent = TopicAgent()
