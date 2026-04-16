"""爆品痛点挖掘 Agent — 三农电商版

功能：输入品类/产品名称 → 分析市场痛点 → 输出痛点报告 + 差异化机会

复用自 CrossClaw competitor_analysis + review_nlp_extractor 架构，
适配三农场景：口感/保鲜/物流/农资效果/价格等痛点聚类。
"""

import json
from dataclasses import dataclass
from typing import Any

from loguru import logger

from app.services.llm_service import llm_service
from app.services.knowledge_base import kb, PAIN_POINT_CATEGORIES
from app.services.sample_library import get_few_shot_samples, format_few_shot_block
from app.services.compliance_engine import compliance_engine


# ─── 系统 Prompt ──────────────────────────────────────

PAIN_POINT_SYSTEM_PROMPT = """你是一位资深三农电商运营专家，擅长分析农产品/农资产品的市场痛点，帮助农户和合作社找到爆品机会。

你的分析维度包括：
1. 口感/品质痛点（消费者最核心关注）
2. 物流/保鲜痛点（生鲜最大障碍）
3. 价格/性价比痛点（价格敏感型市场）
4. 产品真实性痛点（消费信任问题）
5. 售后服务痛点（纠纷和退款问题）
6. 农资效果痛点（仅适用于种子/化肥/农药类目）

分析时请：
- 结合抖音、拼多多、惠农网等三农平台用户评价规律
- 给出具体、可操作的差异化建议
- 语言接地气，符合农村电商氛围
- 严格遵守食品安全宣传规范，不出现违规极限词

【真实数据铁律】
- 所有痛点、机会点、定价建议优先依据输入里的真实知识库事实、投诉数据、价格带和真实样本
- 不得编造销量、退货率、检测报告、赔付比例、资质和库存

请以JSON格式返回分析结果。"""


PAIN_POINT_USER_PROMPT_TEMPLATE = """请对以下农产品/农资进行深度痛点分析：

产品信息：
- 品类：{category}
- 产品名称：{product_name}
- 平台：{platform}
- 月销量级别：{sales_level}
- 竞品描述：{competitor_info}

品类关键词：
{category_keywords}

真实知识库事实：
{fact_block}

平台与投诉事实：
{platform_facts}

请返回严格JSON格式（控制在1500字以内，只返回5条痛点）：
{{
  "product_summary": "产品市场概述（50字内）",
  "top_pain_points": [
    {{
      "rank": 1,
      "pain_point": "具体痛点描述（30字内）",
      "frequency": "高/中/低",
      "sample_reviews": ["典型用户评价示例（20字内）"],
      "opportunity": "差异化机会点（40字内）"
    }}
  ],
  "differentiation_opportunities": [
    {{
      "opportunity": "差异化机会（30字内）",
      "implementation": "落地方式（30字内）"
    }}
  ],
  "pricing_suggestion": {{
    "suggested_price_range": "建议零售价区间（如：29.9-39.9元/5斤）",
    "pricing_strategy": "定价策略（30字内）",
    "anchor_price": "对标锚点（如：超市同品49.9，直播间定29.9）"
  }},
  "keyword_opportunities": ["关键词1", "关键词2", "关键词3"],
  "quick_wins": ["快速优化动作1", "快速优化动作2"]
}}"""


@dataclass
class PainPointRequest:
    category: str                    # 品类
    product_name: str                # 产品名称
    platform: str = "douyin"         # 平台
    sales_level: str = "中等（月销1000-5000单）"
    competitor_info: str = ""        # 竞品信息（可选）


@dataclass
class PainPointReport:
    product_summary: str
    top_pain_points: list[dict[str, Any]]
    differentiation_opportunities: list[dict[str, Any]]
    pricing_suggestion: dict[str, str]
    keyword_opportunities: list[str]
    quick_wins: list[str]
    category_keywords: dict[str, list[str]]  # 从知识库注入
    raw_output: str = ""


class PainPointAgent:
    """爆品痛点挖掘 Agent

    1. 注入三农知识库上下文
    2. 调用 LLM 分析痛点
    3. 合并知识库规则结果
    4. 返回结构化报告
    """

    def __init__(self):
        self._llm = llm_service
        self._kb = kb

    def analyze(self, request: PainPointRequest) -> PainPointReport:
        logger.info(
            "PainPointAgent: 开始分析 category={} product={}",
            request.category, request.product_name
        )

        # 1. 从知识库注入品类上下文
        canonical_category = self._kb.resolve_best_category(request.product_name, request.category)
        category_kw = self._kb.get_category_keywords(canonical_category or request.category)
        category_insights = self._kb.get_category_insights(canonical_category)
        fact_block = self._kb.build_fact_block(canonical_category or request.product_name, request.platform)
        platform_insights = self._kb.get_platform_insights(request.platform)
        pain_cats = list(self._kb.get_pain_point_categories().keys())
        kw_str = "\n".join(
            f"- {kw_type}：{'、'.join(kws[:5])}"
            for kw_type, kws in list(category_kw.items())[:3]
        )
        platform_fact_str = "\n".join(
            f"- {item}"
            for item in (platform_insights.get("facts", [])[:3] + platform_insights.get("generation_rules", [])[:2])
        )

        # 1b. Few-shot 注入：获取真实痛点样本
        sample_key = canonical_category or request.category
        samples = get_few_shot_samples(sample_key, sample_type="pain_point", count=3)
        if len(samples) < 3 and request.product_name != sample_key:
            extra = get_few_shot_samples(request.product_name, sample_type="pain_point", count=3 - len(samples))
            samples.extend(extra)
        few_shot_block = format_few_shot_block(samples, sample_type="pain_point")
        if few_shot_block:
            system_prompt = PAIN_POINT_SYSTEM_PROMPT + "\n\n" + few_shot_block
            logger.info("PainPointAgent: 注入{}条真实痛点样本（品类:{}）", len(samples), sample_key)
        else:
            system_prompt = PAIN_POINT_SYSTEM_PROMPT

        # 2. 构建 Prompt
        user_prompt = PAIN_POINT_USER_PROMPT_TEMPLATE.format(
            category=canonical_category or request.category,
            product_name=request.product_name,
            platform=self._format_platform(request.platform),
            sales_level=request.sales_level,
            competitor_info=request.competitor_info or "；".join(category_insights.get("pain_focus", [])[:3]) or f"市场常见同类{request.category}产品",
            category_keywords=kw_str or "- 产地直发、分级发货、坏果包赔",
            fact_block=fact_block or "- 暂无额外事实，优先分析真实性、物流和售后",
            platform_facts=platform_fact_str or "- 农产品投诉高频集中在货不对板、坏果、缺斤少两",
        )

        # 3. 调用 LLM
        try:
            result = self._llm.chat_json(system_prompt, user_prompt)
        except Exception as exc:
            logger.error("PainPointAgent LLM 调用失败: {}", exc)
            result = self._fallback_analysis(request, pain_cats)

        # 4. 组装报告
        report = PainPointReport(
            product_summary=result.get("product_summary", ""),
            top_pain_points=result.get("top_pain_points", []),
            differentiation_opportunities=result.get("differentiation_opportunities", []),
            pricing_suggestion=result.get("pricing_suggestion", {}),
            keyword_opportunities=result.get("keyword_opportunities", []),
            quick_wins=result.get("quick_wins", []),
            category_keywords=category_kw,
            raw_output=json.dumps(result, ensure_ascii=False),
        )

        # 合规检查：对关键词建议做合规校验（兼容str和dict两种格式）
        safe_kws = []
        for kw in report.keyword_opportunities:
            # LLM有时返回dict（如{"keyword":"xxx"}），统一转成str
            kw_str = kw if isinstance(kw, str) else (
                kw.get("keyword", "") or kw.get("text", "") or str(kw)
            )
            if not kw_str:
                continue
            try:
                check = compliance_engine.check(kw_str, "关键词")
                if isinstance(check, dict):
                    safe_kws.append(check.get("fixed_text", kw_str) if not check.get("passed", True) else kw_str)
                else:
                    safe_kws.append(kw_str)
            except Exception:
                safe_kws.append(kw_str)
        report.keyword_opportunities = safe_kws

        logger.info(
            "PainPointAgent: 分析完成，痛点数量={}",
            len(report.top_pain_points)
        )
        return report

    def _format_platform(self, platform: str) -> str:
        mapping = {
            "douyin": "抖音小店",
            "pinduoduo": "拼多多",
            "huinong": "惠农网",
            "taobao": "淘宝",
            "jd": "京东",
        }
        return mapping.get(platform, platform)

    def _fallback_analysis(self, req: PainPointRequest, pain_cats: list[str]) -> dict:
        """LLM 不可用时的规则兜底分析（使用真实市场数据）"""
        cat_data = self._kb.get_pain_point_categories()
        canonical_category = self._kb.resolve_best_category(req.product_name, req.category)
        insights = self._kb.get_category_insights(canonical_category)
        core_words = self._kb.get_category_core_words(canonical_category or req.category)
        top_pain_points = []
        # 优先从样本库取真实痛点数据
        from app.services.sample_library import get_few_shot_samples
        real_pain = get_few_shot_samples(canonical_category or req.product_name, "pain_point", count=5)
        if len(real_pain) < 3 and req.product_name != (canonical_category or req.product_name):
            real_pain += get_few_shot_samples(req.product_name, "pain_point", count=5 - len(real_pain))
        if len(real_pain) < 3:
            real_pain += get_few_shot_samples("通用", "pain_point", count=5 - len(real_pain))

        pain_focus = insights.get("pain_focus", []) or [data["label"] for _, data in list(cat_data.items())[:5]]
        generic_items = list(cat_data.items())[:5]
        for i, pain_focus_item in enumerate(pain_focus[:5], 1):
            key, data = generic_items[min(i - 1, len(generic_items) - 1)]
            real_sample = real_pain[i - 1] if i - 1 < len(real_pain) else None
            pain_desc = (
                real_sample.get("script", "")[:60]
                if real_sample
                else f"{req.product_name}市场常见{pain_focus_item}问题"
            )
            top_pain_points.append({
                "rank": i,
                "pain_point": pain_desc or f"{req.product_name}{pain_focus_item}",
                "frequency": "高" if i <= 2 else "中",
                "sample_reviews": [real_sample.get("hook_type", data["label"])] if real_sample else [data["label"]],
                "opportunity": insights.get("reply_tips", [data["opportunity"]])[min(i - 1, len(insights.get("reply_tips", [data["opportunity"]])) - 1)],
            })

        # 从知识库获取真实市场定价数据（来源：嘉兴水果市场2024运行报告等）
        pricing = self._kb.get_market_pricing(canonical_category or req.product_name)
        if pricing:
            pricing_suggestion = {
                "suggested_price_range": f"批发均价{pricing['wholesale_avg']}，电商零售参考{pricing['ecom_range']}",
                "pricing_strategy": f"趋势：{pricing['wholesale_trend']}，主推产地直发价格优势",
                "anchor_price": f"品牌溢价参考：{pricing['premium_brand']}",
                "data_source": pricing["source"],
            }
        else:
            pricing_suggestion = {
                "suggested_price_range": f"建议产地直发价格，参考同品类电商均价下浮20-30%",
                "pricing_strategy": f"主推产地直发价格优势，与超市价格形成20-40%差距，突出零中间商",
                "anchor_price": f"用超市同款定价做锚点，直播间价格明显低于超市",
            }

        return {
            "product_summary": insights.get("production_facts", [f"{req.product_name}在{req.category}类目竞争激烈，核心在品质和服务差异化。"])[0],
            "top_pain_points": top_pain_points,
            "differentiation_opportunities": [
                {
                    "opportunity": (insights.get("topic_angles", ["产地溯源透明化"])[0]),
                    "implementation": (insights.get("ecommerce_facts", ["主图和短视频重点拍产地、分级、发货过程"])[0]),
                    "expected_impact": "提升信任和转化",
                },
                {
                    "opportunity": "售后承诺前置",
                    "implementation": (insights.get("reply_tips", ["把坏果包赔和平台处理流程写到主图、详情和直播间"])[0]),
                    "expected_impact": "降低纠纷和差评",
                },
            ],
            "pricing_suggestion": pricing_suggestion,
            "keyword_opportunities": core_words[:3] or [f"{req.product_name}产地直发", f"新鲜{req.product_name}", f"{req.product_name}坏果包赔"],
            "quick_wins": [
                "优化主图增加产地实拍",
                "在标题和详情写清分级标准",
                (insights.get("reply_tips", ["把售后处理流程写前面"])[0]),
            ],
        }


pain_point_agent = PainPointAgent()
