"""评论自动回复 — API 路由"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from app.services.reply_agent import reply_agent, ReplyRequest, BatchReplyRequest

router = APIRouter(prefix="/api/reply", tags=["评论回复"])


async def _auth_optional(authorization: Optional[str] = Header(None)):
    return authorization


class ReplyBody(BaseModel):
    product_name: str = Field(..., examples=["赣南脐橙"])
    comment: str = Field(..., examples=["这个橙子好甜啊！下次还买"])
    origin: str = Field("", examples=["江西赣州"])
    price: str = Field("", examples=["29.9元/5斤"])


class BatchReplyBody(BaseModel):
    product_name: str = Field(..., examples=["赣南脐橙"])
    comments: list[str] = Field(..., examples=[["好甜！", "啥时候发货", "能便宜点吗"]])
    origin: str = Field("", examples=["江西赣州"])
    price: str = Field("", examples=["29.9元/5斤"])


@router.post("/generate")
async def generate_reply(body: ReplyBody):
    """
    单条评论回复生成
    - 自动识别评论类型（好评/差评/催单/砍价/投诉）
    - 返回口语化回复 + 跟进建议
    """
    try:
        req = ReplyRequest(
            product_name=body.product_name,
            comment=body.comment,
            origin=body.origin,
            price=body.price,
        )
        result = reply_agent.generate(req)
        return {
            "code": 0,
            "message": "回复生成完成",
            "data": {
                "comment_type": result.comment_type,
                "sentiment": result.sentiment,
                "urgency": result.urgency,
                "reply": result.reply,
                "reply_short": result.reply_short,
                "follow_up_action": result.follow_up_action,
                "risk_level": result.risk_level,
            },
        }
    except Exception as exc:
        logger.error("评论回复失败: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch")
async def batch_generate_reply(body: BatchReplyBody):
    """
    批量评论回复生成（最多20条）
    """
    if len(body.comments) > 20:
        raise HTTPException(status_code=400, detail="单次最多20条评论")
    try:
        req = BatchReplyRequest(
            product_name=body.product_name,
            comments=body.comments,
            origin=body.origin,
            price=body.price,
        )
        results = reply_agent.batch_generate(req)
        return {
            "code": 0,
            "message": f"批量回复完成，共{len(results)}条",
            "data": [
                {
                    "index": i,
                    "original_comment": body.comments[i] if i < len(body.comments) else "",
                    "comment_type": r.comment_type,
                    "sentiment": r.sentiment,
                    "urgency": r.urgency,
                    "reply": r.reply,
                    "reply_short": r.reply_short,
                    "follow_up_action": r.follow_up_action,
                    "risk_level": r.risk_level,
                }
                for i, r in enumerate(results)
            ],
        }
    except Exception as exc:
        logger.error("批量回复失败: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc))
