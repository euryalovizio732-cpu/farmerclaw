"""全流程自动化 Pipeline — API 路由"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from loguru import logger

from app.services.pipeline_agent import pipeline_agent, PipelineRequest
from app.routers.auth_router import get_current_user_optional

router = APIRouter(prefix="/api/pipeline", tags=["全流程自动化"])


class PipelineRequestBody(BaseModel):
    product_name: str = Field(..., description="产品名称", examples=["赣南脐橙"])
    category: str = Field(..., description="品类", examples=["水果"])
    origin: str = Field("", description="产地", examples=["江西赣州"])
    specification: str = Field("", description="规格/重量", examples=["5斤装"])
    price: str = Field("", description="定价", examples=["29.9元/5斤"])
    core_features: str = Field("", description="核心卖点")
    platform: str = Field("douyin", description="目标平台")
    sales_level: str = Field("中等（月销1000-5000单）", description="月销量级别")
    competitor_info: str = Field("", description="竞品描述（可选）")


@router.post("/run")
async def run_pipeline(
    body: PipelineRequestBody,
    user=Depends(get_current_user_optional),
):
    """
    全流程自动化：痛点挖掘 → Listing生成 → 合规校验

    一次调用，完成全部三个阶段，无需手动跳转。
    返回：痛点报告 + 完整Listing + 合规状态
    """
    # 未登录用户可免费试用（功能完整，无次数限制，内测阶段）
    user_id = user.id if user else "anonymous"
    logger.info("Pipeline 请求: user={} product={}", user_id, body.product_name)

    try:
        req = PipelineRequest(
            product_name=body.product_name,
            category=body.category,
            origin=body.origin,
            specification=body.specification,
            price=body.price,
            core_features=body.core_features,
            platform=body.platform,
            sales_level=body.sales_level,
            competitor_info=body.competitor_info,
        )
        result = pipeline_agent.run(req)

        return {
            "code": 0,
            "message": f"全流程完成，已执行阶段：{', '.join(result.stages_completed)}",
            "data": {
                "product_name": result.product_name,
                "category": result.category,
                "platform": result.platform,
                "stages_completed": result.stages_completed,
                "stages_failed": result.stages_failed,

                "pain_analysis": {
                    "summary": result.pain_point_summary,
                    "top_pain_points": result.top_pain_points,
                    "differentiation_opportunities": result.differentiation_opportunities,
                    "pricing_suggestion": result.pricing_suggestion,
                    "keyword_opportunities": result.keyword_opportunities,
                    "quick_wins": result.quick_wins,
                },

                "listing": {
                    "title": result.title,
                    "subtitle": result.subtitle,
                    "selling_points": result.selling_points,
                    "detail_page": result.detail_page,
                    "main_image_script": result.main_image_script,
                    "video_script": result.video_script,
                    "live_script": result.live_script,
                    "seo_keywords": result.seo_keywords,
                    "hashtags": result.hashtags,
                },

                "compliance": result.compliance,
            },
        }
    except Exception as exc:
        logger.error("Pipeline 执行失败: {}", exc)
        raise HTTPException(status_code=500, detail=f"流程执行失败：{str(exc)}")
