"""投放优化（DOU+）— API 路由"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from app.services.ad_agent import ad_agent, AdRequest

router = APIRouter(prefix="/api/ad", tags=["投放优化"])


async def _auth_optional(authorization: Optional[str] = Header(None)):
    return authorization


class AdBody(BaseModel):
    category: str = Field(..., examples=["水果"])
    product_name: str = Field(..., examples=["赣南脐橙"])
    origin: str = Field("", examples=["江西赣州"])
    price: str = Field("", examples=["29.9元/5斤"])
    video_type: str = Field("口播", examples=["口播"])
    natural_views: int = Field(0, description="自然播放量")
    completion_rate: float = Field(0.0, description="完播率（%）")
    like_rate: float = Field(0.0, description="点赞率（%）")
    comment_rate: float = Field(0.0, description="评论率（%）")
    share_rate: float = Field(0.0, description="分享率（%）")
    duration: int = Field(30, description="视频时长（秒）")
    publish_time: str = Field("", description="发布时间，格式HH:MM")
    followers: int = Field(0, description="账号粉丝数")
    avg_views: int = Field(0, description="历史平均播放量")
    has_violation: str = Field("无", description="近30天是否违规")
    budget: int = Field(300, description="投放预算（元）")


@router.post("/optimize")
async def optimize_ad(body: AdBody):
    """
    DOU+ 投放优化建议
    - 判断视频是否值得投放
    - 给出时间段/人群/预算分配建议
    - 输出置顶话术建议
    """
    try:
        req = AdRequest(
            category=body.category,
            product_name=body.product_name,
            origin=body.origin,
            price=body.price,
            video_type=body.video_type,
            natural_views=body.natural_views,
            completion_rate=body.completion_rate,
            like_rate=body.like_rate,
            comment_rate=body.comment_rate,
            share_rate=body.share_rate,
            duration=body.duration,
            publish_time=body.publish_time,
            followers=body.followers,
            avg_views=body.avg_views,
            has_violation=body.has_violation,
            budget=body.budget,
        )
        result = ad_agent.optimize(req)
        return {
            "code": 0,
            "message": "投放分析完成",
            "data": {
                "should_boost": result.should_boost,
                "should_boost_reason": result.should_boost_reason,
                "score": result.score,
                "score_breakdown": result.score_breakdown,
                "timing": result.timing,
                "target_audience": result.target_audience,
                "budget_plan": result.budget_plan,
                "objective": result.objective,
                "copy_suggestion": result.copy_suggestion,
                "risk": result.risk,
            },
        }
    except Exception as exc:
        logger.error("投放分析失败: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc))
