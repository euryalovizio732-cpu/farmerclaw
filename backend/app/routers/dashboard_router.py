"""数据看板 — API 路由（真实DB数据）"""

from collections import Counter
from fastapi import APIRouter
from loguru import logger
from sqlalchemy import select, func

router = APIRouter(prefix="/api/dashboard", tags=["数据看板"])

PLATFORM_LABELS = {
    "douyin": "抖音小店",
    "pinduoduo": "拼多多",
    "huinong": "惠农网",
    "taobao": "淘宝",
    "jd": "京东",
}


async def _query_real_stats() -> dict:
    """从DB查询真实统计数据"""
    from app.database import async_session
    from app.models.records import PainPointRecord, ListingRecord, ContentPackRecord
    from app.models.user import User

    async with async_session() as session:
        # 总次数
        total_analyses = (await session.execute(select(func.count()).select_from(PainPointRecord))).scalar() or 0
        total_listings = (await session.execute(select(func.count()).select_from(ListingRecord))).scalar() or 0
        total_packs = (await session.execute(select(func.count()).select_from(ContentPackRecord))).scalar() or 0
        total_users = (await session.execute(select(func.count()).select_from(User))).scalar() or 0

        # 合规通过率
        total_lr = total_listings
        if total_lr > 0:
            passed = (await session.execute(
                select(func.count()).select_from(ListingRecord).where(ListingRecord.compliance_passed == True)
            )).scalar() or 0
            compliance_rate = round(passed / total_lr * 100, 1)
        else:
            compliance_rate = 100.0

        # 品类分布（Listing记录）
        cat_rows = (await session.execute(
            select(ListingRecord.category, func.count().label("cnt"))
            .group_by(ListingRecord.category)
            .order_by(func.count().desc())
            .limit(5)
        )).all()
        top_categories = [{"name": r[0], "count": r[1]} for r in cat_rows]

        # 平台分布
        plat_rows = (await session.execute(
            select(ListingRecord.platform, func.count().label("cnt"))
            .group_by(ListingRecord.platform)
            .order_by(func.count().desc())
        )).all()
        top_platforms = [
            {"name": PLATFORM_LABELS.get(r[0], r[0]), "count": r[1]}
            for r in plat_rows
        ]

        # 最近10条 Listing 记录
        recent_rows = (await session.execute(
            select(ListingRecord)
            .order_by(ListingRecord.created_at.desc())
            .limit(10)
        )).scalars().all()
        recent_listings = [
            {
                "product": r.product_name,
                "category": r.category,
                "platform": PLATFORM_LABELS.get(r.platform, r.platform),
                "compliance": r.compliance_passed,
                "title": r.title[:30] if r.title else "",
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
            }
            for r in recent_rows
        ]

        # 最近10条内容包记录
        pack_rows = (await session.execute(
            select(ContentPackRecord)
            .order_by(ContentPackRecord.created_at.desc())
            .limit(10)
        )).scalars().all()
        recent_packs = [
            {
                "product": r.product_name,
                "category": r.category,
                "origin": r.origin,
                "topics": r.topics_count,
                "scripts": r.scripts_count,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
            }
            for r in pack_rows
        ]

    return {
        "total_analyses": total_analyses,
        "total_listings": total_listings,
        "total_packs": total_packs,
        "total_users": total_users,
        "compliance_pass_rate": compliance_rate,
        "top_categories": top_categories,
        "top_platforms": top_platforms,
        "recent_listings": recent_listings,
        "recent_packs": recent_packs,
    }


def _empty_stats() -> dict:
    return {
        "total_analyses": 0, "total_listings": 0,
        "total_packs": 0, "total_users": 0,
        "compliance_pass_rate": 100.0,
        "top_categories": [], "top_platforms": [],
        "recent_listings": [], "recent_packs": [],
    }


@router.get("/stats")
async def get_stats():
    """获取使用统计（真实DB数据）"""
    try:
        from app.database import async_session as _session
        if _session is None:
            return {"code": 0, "data": _empty_stats()}
        data = await _query_real_stats()
        return {"code": 0, "data": data}
    except Exception as exc:
        logger.warning("看板数据查询失败，返回空: {}", exc)
        return {"code": 0, "data": _empty_stats()}


@router.get("/history")
async def get_history(days: int = 30, limit: int = 50):
    """
    最近 N 天内容历史回查
    返回：内容包 + Listing + 痛点分析，按时间倒序
    """
    from datetime import datetime, timedelta
    from app.database import async_session
    from app.models.records import PainPointRecord, ListingRecord, ContentPackRecord

    cutoff = datetime.utcnow() - timedelta(days=days)

    try:
        async with async_session() as session:
            # 内容包
            pack_rows = (await session.execute(
                select(ContentPackRecord)
                .where(ContentPackRecord.created_at >= cutoff)
                .order_by(ContentPackRecord.created_at.desc())
                .limit(limit)
            )).scalars().all()

            # Listing
            listing_rows = (await session.execute(
                select(ListingRecord)
                .where(ListingRecord.created_at >= cutoff)
                .order_by(ListingRecord.created_at.desc())
                .limit(limit)
            )).scalars().all()

            # 痛点分析
            pp_rows = (await session.execute(
                select(PainPointRecord)
                .where(PainPointRecord.created_at >= cutoff)
                .order_by(PainPointRecord.created_at.desc())
                .limit(limit)
            )).scalars().all()

        packs = [
            {
                "type": "content_pack",
                "id": r.id,
                "product": r.product_name,
                "category": r.category,
                "origin": r.origin or "",
                "topics": r.topics_count,
                "scripts": r.scripts_count,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                "date_only": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            }
            for r in pack_rows
        ]
        listings = [
            {
                "type": "listing",
                "id": r.id,
                "product": r.product_name,
                "category": r.category,
                "platform": PLATFORM_LABELS.get(r.platform, r.platform),
                "title": r.title[:40] if r.title else "",
                "compliance": r.compliance_passed,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                "date_only": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            }
            for r in listing_rows
        ]
        pp_list = [
            {
                "type": "pain_point",
                "id": r.id,
                "product": r.product_name,
                "category": r.category,
                "platform": PLATFORM_LABELS.get(r.platform, r.platform),
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                "date_only": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
            }
            for r in pp_rows
        ]

        # 合并按时间倒序
        all_records = sorted(packs + listings + pp_list, key=lambda x: x["created_at"], reverse=True)

        return {
            "code": 0,
            "data": {
                "days": days,
                "total": len(all_records),
                "records": all_records,
                "summary": {
                    "content_packs": len(packs),
                    "listings": len(listings),
                    "pain_points": len(pp_list),
                },
            },
        }
    except Exception as exc:
        logger.warning("历史查询失败: {}", exc)
        return {"code": 0, "data": {"days": days, "total": 0, "records": [], "summary": {}}}


@router.get("/history/detail")
async def get_history_detail(record_type: str, record_id: int):
    """获取某条历史记录的完整结果，供前端查看详情"""
    import json as _json
    from app.database import async_session
    from app.models.records import PainPointRecord, ListingRecord, ContentPackRecord

    model_map = {
        "listing": ListingRecord,
        "pain_point": PainPointRecord,
        "content_pack": ContentPackRecord,
    }
    model = model_map.get(record_type)
    if not model:
        return {"code": 1, "message": f"未知类型: {record_type}"}

    try:
        async with async_session() as session:
            row = (await session.execute(
                select(model).where(model.id == record_id)
            )).scalar_one_or_none()

        if not row:
            return {"code": 1, "message": "记录不存在"}

        if record_type == "listing":
            # video_script / live_script 可能是 JSON 字符串
            def _parse(val):
                if isinstance(val, str):
                    try:
                        return _json.loads(val)
                    except Exception:
                        return val
                return val

            data = {
                "title": row.title,
                "selling_points": row.selling_points or [],
                "detail_page": _parse(row.detail_page),
                "video_script": _parse(row.video_script),
                "live_script": _parse(row.live_script),
                "compliance_passed": row.compliance_passed,
                "compliance_issues": row.compliance_issues or [],
            }
        elif record_type == "pain_point":
            data = {
                "pain_points": row.pain_points or [],
                "opportunities": row.opportunities or "",
                "pricing_suggestion": row.pricing_suggestion or "",
            }
        elif record_type == "content_pack":
            result_payload = getattr(row, "result_payload", None) or {}
            request_payload = getattr(row, "request_payload", None) or {}
            if result_payload:
                data = {
                    **result_payload,
                    "request_payload": request_payload,
                    "topics_count": row.topics_count,
                    "scripts_count": row.scripts_count,
                    "stages_completed": row.stages_completed or result_payload.get("stages_completed", []),
                }
            else:
                data = {
                    "topics_count": row.topics_count,
                    "scripts_count": row.scripts_count,
                    "stages_completed": row.stages_completed or [],
                    "request_payload": request_payload,
                    "topics": [],
                    "scripts": [],
                    "live_modules": {},
                    "hashtags": [],
                    "today": {},
                    "history_note": "这条记录生成于完整存档功能上线前，暂时只有概要信息。",
                }
        else:
            data = {}

        data["product_name"] = row.product_name
        data["category"] = row.category
        data["created_at"] = row.created_at.strftime("%Y-%m-%d %H:%M") if row.created_at else ""

        return {"code": 0, "data": data}
    except Exception as exc:
        logger.warning("历史详情查询失败: {}", exc)
        return {"code": 1, "message": str(exc)}


@router.get("/knowledge-base/stats")
async def get_kb_stats():
    """知识库统计（含样本库状态）"""
    from app.services.knowledge_base import CATEGORY_KEYWORDS, PAIN_POINT_CATEGORIES, LIVE_MODULES, DOUYIN_HOOK_PATTERNS
    from app.services.compliance_engine import RULES
    from app.services.sample_library import get_sample_stats

    total_keywords = sum(
        len(kws) for cat_data in CATEGORY_KEYWORDS.values()
        for kws in cat_data.values()
    )
    total_live_modules = sum(len(v) for v in LIVE_MODULES.values())
    sample_stats = get_sample_stats()

    return {
        "code": 0,
        "data": {
            "categories": len(CATEGORY_KEYWORDS),
            "total_keywords": total_keywords,
            "pain_point_categories": len(PAIN_POINT_CATEGORIES),
            "compliance_rules": len(RULES),
            "listing_templates": 4,
            "live_modules": total_live_modules,
            "hook_patterns": len(DOUYIN_HOOK_PATTERNS),
            "season_calendar_months": 12,
            "sample_library": {
                "total_samples": sample_stats["total_samples"],
                "validated_samples": sample_stats["validated_samples"],
                "categories_with_samples": sample_stats["categories_with_samples"],
                "is_ready": sample_stats["is_ready"],
            },
        },
    }
