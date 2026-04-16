"""爆品痛点挖掘 — API 路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.pain_point_agent import pain_point_agent, PainPointRequest
from app.models.records import PainPointRecord

router = APIRouter(prefix="/api/pain-point", tags=["痛点挖掘"])


class PainPointRequestBody(BaseModel):
    category: str = Field(..., description="品类（水果/蔬菜/粮油/种子化肥）", examples=["水果"])
    product_name: str = Field(..., description="产品名称", examples=["脐橙"])
    platform: str = Field("douyin", description="目标平台", examples=["douyin"])
    sales_level: str = Field("中等（月销1000-5000单）", description="月销量级别")
    competitor_info: str = Field("", description="竞品描述（可选）")


@router.post("/analyze")
async def analyze_pain_points(body: PainPointRequestBody):
    """
    爆品痛点挖掘分析

    - 输入品类和产品名称
    - AI自动分析TOP10痛点
    - 返回差异化机会 + 定价建议 + 关键词机会
    """
    try:
        req = PainPointRequest(
            category=body.category,
            product_name=body.product_name,
            platform=body.platform,
            sales_level=body.sales_level,
            competitor_info=body.competitor_info,
        )
        report = pain_point_agent.analyze(req)

        # 异步写库（失败不影响响应）
        try:
            from app.database import async_session
            if async_session:
                async with async_session() as session:
                    record = PainPointRecord(
                        category=body.category,
                        product_name=body.product_name,
                        platform=body.platform,
                        pain_points=report.top_pain_points,
                        opportunities=str(report.differentiation_opportunities),
                        pricing_suggestion=str(report.pricing_suggestion),
                    )
                    session.add(record)
                    await session.commit()
        except Exception as db_exc:
            logger.warning("痛点记录写库失败（不影响结果）: {}", db_exc)

        return {
            "code": 0,
            "message": "分析完成",
            "data": {
                "product_summary": report.product_summary,
                "top_pain_points": report.top_pain_points,
                "differentiation_opportunities": report.differentiation_opportunities,
                "pricing_suggestion": report.pricing_suggestion,
                "keyword_opportunities": report.keyword_opportunities,
                "quick_wins": report.quick_wins,
                "category_keywords": report.category_keywords,
            },
        }
    except Exception as exc:
        logger.error("痛点分析失败: {}", exc)
        raise HTTPException(status_code=500, detail=f"分析失败：{str(exc)}")


@router.get("/categories")
async def get_categories():
    """获取支持的品类列表"""
    from app.services.knowledge_base import kb
    return {
        "code": 0,
        "data": kb.get_all_categories(),
    }
