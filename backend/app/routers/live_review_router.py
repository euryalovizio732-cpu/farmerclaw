"""直播复盘 — API 路由"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from app.services.live_review_agent import live_review_agent, LiveReviewRequest

router = APIRouter(prefix="/api/live-review", tags=["直播复盘"])


class LiveReviewBody(BaseModel):
    category: str = Field(..., examples=["水果"])
    product_name: str = Field(..., examples=["赣南脐橙"])
    duration: int = Field(120, description="直播时长（分钟）")
    peak_viewers: int = Field(0, description="最高同时在线人数")
    avg_viewers: int = Field(0, description="平均在线人数")
    comments: int = Field(0, description="评论数")
    likes: int = Field(0, description="点赞数")
    orders: int = Field(0, description="下单人数")
    gmv: float = Field(0.0, description="成交金额（元）")
    refund_rate: float = Field(0.0, description="退款率（%）")
    script_notes: str = Field("", description="话术/节奏描述")
    merchant_notes: str = Field("", description="商家自述问题")


async def _get_user_optional(authorization: Optional[str] = Header(None)):
    """可选认证"""
    return authorization


@router.post("/analyze")
async def analyze_live(body: LiveReviewBody, auth: Optional[str] = Depends(_get_user_optional)):
    """
    直播复盘分析
    - 输入：直播数据 + 商家自述
    - 输出：问题诊断 + 改进建议 + 下场行动计划
    """
    try:
        req = LiveReviewRequest(
            category=body.category,
            product_name=body.product_name,
            duration=body.duration,
            peak_viewers=body.peak_viewers,
            avg_viewers=body.avg_viewers,
            comments=body.comments,
            likes=body.likes,
            orders=body.orders,
            gmv=body.gmv,
            refund_rate=body.refund_rate,
            script_notes=body.script_notes,
            merchant_notes=body.merchant_notes,
        )
        result = live_review_agent.analyze(req)
        return {
            "code": 0,
            "message": "复盘分析完成",
            "data": {
                "overall_score": result.overall_score,
                "score_reason": result.score_reason,
                "funnel": result.funnel,
                "problems": result.problems,
                "improvements": result.improvements,
                "next_session_plan": result.next_session_plan,
                "highlight": result.highlight,
            },
        }
    except Exception as exc:
        logger.error("直播复盘失败: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc))
