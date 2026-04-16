"""三农 Listing 生成 — API 路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.listing_agent import listing_agent, ListingRequest
from app.services.compliance_engine import compliance_engine
from app.models.records import ListingRecord

router = APIRouter(prefix="/api/listing", tags=["Listing生成"])


class ListingRequestBody(BaseModel):
    product_name: str = Field(..., description="产品名称", examples=["赣南脐橙"])
    category: str = Field(..., description="品类", examples=["水果"])
    origin: str = Field("", description="产地", examples=["江西赣州"])
    specification: str = Field("", description="规格/重量", examples=["5斤装"])
    price: str = Field("", description="定价", examples=["29.9元/5斤"])
    core_features: str = Field("", description="核心卖点描述", examples=["高糖度，皮薄汁多"])
    platform: str = Field("douyin", description="目标平台")
    pain_points_summary: str = Field("", description="痛点摘要（来自痛点分析，可选）")


class ComplianceCheckBody(BaseModel):
    title: str = Field(..., description="标题文本")
    content: str = Field("", description="正文内容")
    platform: str = Field("douyin", description="平台")


@router.post("/generate")
async def generate_listing(body: ListingRequestBody):
    """
    一键生成三农全套 Listing

    - 标题 + 副标题
    - 5条卖点
    - 详情页文案（产品介绍/产地故事/品质证明/配送/售后）
    - 5张主图脚本
    - 30秒短视频口播
    - 完整直播话术（开场/产品介绍/催单/成交）
    - 合规检测报告
    """
    try:
        req = ListingRequest(
            product_name=body.product_name,
            category=body.category,
            origin=body.origin,
            specification=body.specification,
            price=body.price,
            core_features=body.core_features,
            platform=body.platform,
            pain_points_summary=body.pain_points_summary,
        )
        result = listing_agent.generate(req)

        # 写库（失败不影响响应）
        try:
            from app.database import async_session
            if async_session:
                async with async_session() as session:
                    record = ListingRecord(
                        product_name=body.product_name,
                        category=body.category,
                        platform=body.platform,
                        title=result.title,
                        selling_points=result.selling_points,
                        detail_page=str(result.detail_page),
                        video_script=result.video_script.get("full_script", ""),
                        live_script=str(result.live_script),
                        compliance_passed=result.compliance.get("passed", True),
                        compliance_issues=result.compliance.get("issues", []),
                    )
                    session.add(record)
                    await session.commit()
        except Exception as db_exc:
            logger.warning("Listing记录写库失败: {}", db_exc)

        return {
            "code": 0,
            "message": "生成成功",
            "data": {
                "title": result.title,
                "subtitle": result.subtitle,
                "selling_points": result.selling_points,
                "detail_page": result.detail_page,
                "main_image_script": result.main_image_script,
                "video_script": result.video_script,
                "live_script": result.live_script,
                "seo_keywords": result.seo_keywords,
                "hashtags": result.hashtags,
                "compliance": result.compliance,
                "platform": result.platform,
            },
        }
    except Exception as exc:
        logger.error("Listing 生成失败: {}", exc)
        raise HTTPException(status_code=500, detail=f"生成失败：{str(exc)}")


@router.post("/compliance-check")
async def check_compliance(body: ComplianceCheckBody):
    """
    独立合规检测接口

    检测文本中是否含有违规词（极限词、虚假宣传、联系方式等）
    """
    try:
        result = compliance_engine.check_listing(
            title=body.title,
            selling_points=[body.content] if body.content else [],
            platform=body.platform,
        )
        return {
            "code": 0,
            "message": "检测完成",
            "data": result,
        }
    except Exception as exc:
        logger.error("合规检测失败: {}", exc)
        raise HTTPException(status_code=500, detail=f"检测失败：{str(exc)}")


@router.get("/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    return {
        "code": 0,
        "data": [
            {"value": "douyin", "label": "抖音小店", "title_limit": 30},
            {"value": "pinduoduo", "label": "拼多多", "title_limit": 60},
            {"value": "huinong", "label": "惠农网", "title_limit": 50},
            {"value": "taobao", "label": "淘宝", "title_limit": 60},
            {"value": "jd", "label": "京东", "title_limit": 60},
        ],
    }
