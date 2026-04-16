"""抖音三农选题 — API 路由"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.topic_agent import topic_agent, TopicRequest

router = APIRouter(prefix="/api/topic", tags=["选题生成"])


class TopicRequestBody(BaseModel):
    product_name: str = Field(..., description="产品名称", examples=["赣南脐橙"])
    category: str = Field(..., description="品类", examples=["水果"])
    origin: str = Field("", description="产地", examples=["江西赣州"])
    core_features: str = Field("", description="核心卖点描述（可选）")


@router.post("/generate")
async def generate_topics(body: TopicRequestBody):
    """
    生成3条抖音爆款选题

    - 每条包含：选题标题、封面建议、拍摄角度、核心矛盾、预估完播率
    - 自动注入当前节气/时令信息
    - 自动合规校验标题
    """
    try:
        req = TopicRequest(
            product_name=body.product_name,
            category=body.category,
            origin=body.origin,
            core_features=body.core_features,
        )
        result = topic_agent.generate(req)

        return {
            "code": 0,
            "message": "选题生成成功",
            "data": {
                "today_tip": result.today_tip,
                "topics": result.topics,
                "hashtags": result.hashtags,
                "season_info": result.season_info,
            },
        }
    except Exception as exc:
        logger.error("选题生成失败: {}", exc)
        raise HTTPException(status_code=500, detail=f"选题生成失败：{str(exc)}")
