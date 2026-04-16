"""全流程自动化 Pipeline Agent

痛点挖掘 → Listing生成 → 合规校验 全自动衔接，无需用户手动跳转。

工作流：
  1. 接收产品基础信息
  2. 自动运行 PainPointAgent
  3. 提取痛点摘要，自动注入 ListingAgent
  4. 返回合并报告（痛点 + Listing + 合规状态）
"""

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from app.services.pain_point_agent import pain_point_agent, PainPointRequest
from app.services.listing_agent import listing_agent, ListingRequest


@dataclass
class PipelineRequest:
    product_name: str
    category: str
    origin: str = ""
    specification: str = ""
    price: str = ""
    core_features: str = ""
    platform: str = "douyin"
    sales_level: str = "中等（月销1000-5000单）"
    competitor_info: str = ""


@dataclass
class PipelineResult:
    product_name: str
    category: str
    platform: str

    # 阶段1：痛点分析
    pain_point_summary: str = ""
    top_pain_points: list[dict[str, Any]] = field(default_factory=list)
    differentiation_opportunities: list[dict[str, Any]] = field(default_factory=list)
    pricing_suggestion: dict[str, str] = field(default_factory=dict)
    keyword_opportunities: list[str] = field(default_factory=list)
    quick_wins: list[str] = field(default_factory=list)

    # 阶段2：Listing生成
    title: str = ""
    subtitle: str = ""
    selling_points: list[str] = field(default_factory=list)
    detail_page: dict[str, str] = field(default_factory=dict)
    main_image_script: dict[str, str] = field(default_factory=dict)
    video_script: dict[str, str] = field(default_factory=dict)
    live_script: dict[str, str] = field(default_factory=dict)
    seo_keywords: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)

    # 合规状态
    compliance: dict[str, Any] = field(default_factory=dict)

    # 流程元信息
    stages_completed: list[str] = field(default_factory=list)
    stages_failed: list[str] = field(default_factory=list)


class PipelineAgent:
    """全流程 Pipeline Agent

    串联 PainPointAgent → ListingAgent，实现零人工干预的全自动化。
    单个阶段失败不中断后续阶段（降级继续执行）。
    """

    def run(self, request: PipelineRequest) -> PipelineResult:
        logger.info(
            "PipelineAgent 启动: product={} category={} platform={}",
            request.product_name, request.category, request.platform,
        )

        result = PipelineResult(
            product_name=request.product_name,
            category=request.category,
            platform=request.platform,
        )

        # ── Stage 1: 痛点挖掘 ──────────────────────────────
        pain_summary = self._run_pain_point_stage(request, result)

        # ── Stage 2: Listing 生成（注入痛点摘要） ──────────
        self._run_listing_stage(request, result, pain_summary)

        logger.info(
            "PipelineAgent 完成: stages_ok={} stages_fail={}",
            result.stages_completed, result.stages_failed,
        )
        return result

    # ──────────────────────────────────────────────────────

    def _run_pain_point_stage(
        self, request: PipelineRequest, result: PipelineResult
    ) -> str:
        """运行痛点分析，返回供 Listing Agent 使用的摘要字符串"""
        try:
            pp_req = PainPointRequest(
                category=request.category,
                product_name=request.product_name,
                platform=request.platform,
                sales_level=request.sales_level,
                competitor_info=request.competitor_info,
            )
            pp_report = pain_point_agent.analyze(pp_req)

            result.pain_point_summary = pp_report.product_summary
            result.top_pain_points = pp_report.top_pain_points
            result.differentiation_opportunities = pp_report.differentiation_opportunities
            result.pricing_suggestion = pp_report.pricing_suggestion
            result.keyword_opportunities = pp_report.keyword_opportunities
            result.quick_wins = pp_report.quick_wins
            result.stages_completed.append("pain_point")

            # 自动生成摘要传递给下一阶段
            top3 = [p.get("pain_point", "") for p in pp_report.top_pain_points[:3]]
            pain_summary = "；".join(top3) if top3 else ""
            logger.info("Stage1 痛点分析完成，提取摘要: {}", pain_summary[:60])
            return pain_summary

        except Exception as exc:
            logger.error("Stage1 痛点分析失败: {}", exc)
            result.stages_failed.append("pain_point")
            return ""

    def _run_listing_stage(
        self,
        request: PipelineRequest,
        result: PipelineResult,
        pain_summary: str,
    ) -> None:
        """运行 Listing 生成，自动注入上一阶段痛点摘要"""
        try:
            listing_req = ListingRequest(
                product_name=request.product_name,
                category=request.category,
                origin=request.origin,
                specification=request.specification,
                price=request.price,
                core_features=request.core_features,
                platform=request.platform,
                pain_points_summary=pain_summary,
            )
            listing_result = listing_agent.generate(listing_req)

            result.title = listing_result.title
            result.subtitle = listing_result.subtitle
            result.selling_points = listing_result.selling_points
            result.detail_page = listing_result.detail_page
            result.main_image_script = listing_result.main_image_script
            result.video_script = listing_result.video_script
            result.live_script = listing_result.live_script
            result.seo_keywords = listing_result.seo_keywords
            result.hashtags = listing_result.hashtags
            result.compliance = listing_result.compliance
            result.stages_completed.append("listing")

            logger.info("Stage2 Listing生成完成: title={}", result.title[:30])

        except Exception as exc:
            logger.error("Stage2 Listing生成失败: {}", exc)
            result.stages_failed.append("listing")


pipeline_agent = PipelineAgent()
