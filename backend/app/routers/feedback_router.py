"""用户反馈 — API 路由
商家每次对生成内容评价「直接可用/需修改/不能用」
这是迭代 Prompt 的核心数据来源。
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from loguru import logger
from sqlalchemy import select, func

router = APIRouter(prefix="/api/feedback", tags=["反馈"])


class FeedbackBody(BaseModel):
    content_type: str = Field(..., examples=["script"])
    content_id: str = Field("", examples=["script_1"])
    product_name: str = Field("", examples=["赣南脐橙"])
    category: str = Field("", examples=["水果"])
    rating: str = Field(..., examples=["usable"])   # usable / needs_edit / unusable
    edited_text: str = Field("", description="商家改过的版本（最宝贵的数据）")
    comment: str = Field("", description="简短反馈")


@router.post("/submit")
async def submit_feedback(body: FeedbackBody):
    """提交单条内容反馈"""
    try:
        from app.database import async_session
        from app.models.records import FeedbackRecord

        async with async_session() as session:
            rec = FeedbackRecord(
                content_type=body.content_type,
                content_id=body.content_id,
                product_name=body.product_name,
                category=body.category,
                rating=body.rating,
                edited_text=body.edited_text,
                comment=body.comment,
            )
            session.add(rec)
            await session.commit()

        # ── 自动沉淀到样本库 ──
        # 「直接可用」→ 原文入库；「改了能用」且有编辑文本 → 编辑版入库
        try:
            from app.services.sample_library import add_validated_sample
            if body.rating == "usable" and body.edited_text:
                add_validated_sample(
                    category=body.category or "通用",
                    script=body.edited_text,
                    source=f"merchant_feedback:{body.product_name}",
                )
                logger.info("样本自动入库(原文): category={}", body.category)
            elif body.rating == "needs_edit" and body.edited_text:
                add_validated_sample(
                    category=body.category or "通用",
                    script=body.edited_text,
                    source=f"merchant_edited:{body.product_name}",
                )
                logger.info("样本自动入库(编辑版): category={}", body.category)
        except Exception as deposit_exc:
            logger.warning("样本沉淀失败: {}", deposit_exc)

        logger.info("反馈收录: type={} rating={} product={}", body.content_type, body.rating, body.product_name)
        return {"code": 0, "message": "反馈已记录，感谢你的帮助！"}
    except Exception as exc:
        logger.warning("反馈保存失败: {}", exc)
        return {"code": 0, "message": "反馈已收到"}


@router.get("/stats")
async def get_feedback_stats():
    """反馈统计（用于迭代 Prompt 的决策依据）"""
    try:
        from app.database import async_session
        from app.models.records import FeedbackRecord

        async with async_session() as session:
            total = (await session.execute(
                select(func.count()).select_from(FeedbackRecord)
            )).scalar() or 0

            usable = (await session.execute(
                select(func.count()).select_from(FeedbackRecord)
                .where(FeedbackRecord.rating == "usable")
            )).scalar() or 0

            needs_edit = (await session.execute(
                select(func.count()).select_from(FeedbackRecord)
                .where(FeedbackRecord.rating == "needs_edit")
            )).scalar() or 0

            unusable = (await session.execute(
                select(func.count()).select_from(FeedbackRecord)
                .where(FeedbackRecord.rating == "unusable")
            )).scalar() or 0

            edited_samples = (await session.execute(
                select(FeedbackRecord)
                .where(FeedbackRecord.edited_text != "")
                .order_by(FeedbackRecord.created_at.desc())
                .limit(10)
            )).scalars().all()

        usable_rate = round(usable / total * 100, 1) if total else 0

        return {
            "code": 0,
            "data": {
                "total": total,
                "usable": usable,
                "needs_edit": needs_edit,
                "unusable": unusable,
                "usable_rate": usable_rate,
                "target_rate": 70,
                "gap": max(0, 70 - usable_rate),
                "edited_samples": [
                    {
                        "product": r.product_name,
                        "category": r.category,
                        "edited_text": r.edited_text[:200],
                        "comment": r.comment,
                        "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                    }
                    for r in edited_samples
                ],
            },
        }
    except Exception as exc:
        logger.warning("反馈统计失败: {}", exc)
        return {"code": 0, "data": {"total": 0, "usable_rate": 0, "target_rate": 70}}
