"""今日内容包 — API 路由"""

import re as _re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.services.content_pack_agent import content_pack_agent, ContentPackRequest
from app.services.knowledge_base import kb
from app.models.records import ContentPackRecord

router = APIRouter(prefix="/api/content-pack", tags=["今日内容包"])

_QUICK_PARSE_SYSTEM = """你是一个信息提取助手。从用户的一句话里提取农产品信息，返回JSON。

字段说明：
- product_name: 产品名称（必须提取，例如"赣南脐橙"）
- category: 品类，只能是以下之一：脐橙/苹果/草莓/粮油/蔬菜/蓝莓/樱桃/猕猴桃/芒果/桃子/葡萄/西瓜/沃柑/石榴/其他水果/其他农产品
- origin: 产地（省市或地名，没有则留空）
- price: 价格（保留原始描述，没有则留空）
- core_features: 核心卖点（从描述中提炼，没有则留空）

严格返回JSON，不要多余内容。"""

_QUICK_PARSE_PROMPT = "请从以下描述中提取产品信息：\n{text}"

_CATEGORY_MAP = {
    "脐橙": "脐橙", "橙子": "脐橙", "赣南橙": "脐橙", "橙": "脐橙", "橘": "脐橙",
    "苹果": "苹果", "冰糖心": "苹果", "洛川": "苹果", "烟台": "苹果",
    "草莓": "草莓", "丹东草莓": "草莓",
    "樱桃": "樱桃", "大樱桃": "樱桃", "车厘子": "樱桃",
    "蓝莓": "蓝莓",
    "猕猴桃": "猕猴桃", "奇异果": "猕猴桃",
    "芒果": "芒果", "攀枝花芒果": "芒果",
    "桃子": "桃子", "蟠桃": "桃子", "水蜜桃": "桃子",
    "葡萄": "葡萄", "巨峰": "葡萄", "阳光玫瑰": "葡萄",
    "西瓜": "西瓜",
    "沃柑": "沃柑",
    "石榴": "石榴", "突尼斯软籽石榴": "石榴",
    "大米": "粮油", "米": "粮油", "小麦": "粮油", "粮": "粮油", "五常": "粮油",
    "蔬菜": "蔬菜", "菜": "蔬菜", "蒜": "蔬菜", "姜": "蔬菜",
}

_ORIGIN_KEYWORDS = [
    "江西", "赣南", "赣州", "陕西", "四川", "攀枝花", "云南", "广西",
    "辽宁", "丹东", "大连", "山东", "烟台", "黑龙江", "五常", "贵州",
    "湖南", "湖北", "安徽", "浙江", "广东", "福建", "海南", "内蒙古",
]

def _rule_parse(text: str) -> dict | None:
    """规则解析，覆盖90%常见输入，不依赖LLM"""
    result: dict = {"product_name": "", "category": "", "origin": "", "price": "", "core_features": ""}

    # 品类匹配（按长度降序，优先匹配长词）
    for keyword in sorted(_CATEGORY_MAP.keys(), key=len, reverse=True):
        if keyword in text:
            result["category"] = _CATEGORY_MAP[keyword]
            break

    # 产品名：取最长匹配的品类关键词前面的修饰词
    product_match = _re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,10}(?=' + '|'.join(
        _re.escape(k) for k in sorted(_CATEGORY_MAP.keys(), key=len, reverse=True) if len(k) >= 2
    ) + r')', text)
    if product_match and result["category"]:
        full_name_match = _re.search(r'([\u4e00-\u9fa5]{2,8}(' + '|'.join(
            _re.escape(k) for k in sorted(_CATEGORY_MAP.keys(), key=len, reverse=True)
        ) + r'))', text)
        if full_name_match:
            result["product_name"] = full_name_match.group(1)
    if not result["product_name"] and result["category"]:
        # 直接用品类词找最近的完整词组
        for kw in sorted(_CATEGORY_MAP.keys(), key=len, reverse=True):
            if kw in text:
                idx = text.index(kw)
                start = max(0, idx - 4)
                result["product_name"] = text[start:idx + len(kw)].strip()
                break

    # 价格：匹配"数字元/斤""数字元5斤"等格式
    price_match = _re.search(r'[0-9]+\.?[0-9]*\s*元[^，,。\s]{0,6}', text)
    if price_match:
        result["price"] = price_match.group(0).strip()

    # 产地：匹配已知产地关键词
    for origin_kw in sorted(_ORIGIN_KEYWORDS, key=len, reverse=True):
        if origin_kw in text:
            result["origin"] = origin_kw
            break

    # 清除product_name中的口语前缀
    prefixes = ["我卖", "卖的是", "主要卖", "在卖", "帮卖", "我们卖", "专卖", "出售"]
    pn = result["product_name"].strip()
    for prefix in prefixes:
        if pn.startswith(prefix):
            pn = pn[len(prefix):].strip()
    result["product_name"] = pn
    result["category"] = result["category"].strip()

    # 判断解析是否足够（至少有产品名或品类）
    if not result["product_name"] and not result["category"]:
        return None
    if not result["product_name"]:
        result["product_name"] = result["category"]
    return result


@router.post("/quick-parse")
async def quick_parse(body: dict):
    """
    一句话解析产品信息（规则优先，LLM兜底）
    输入: {"text": "我卖赣南脐橙，29.9元5斤，江西赣州发货，皮薄汁多"}
    输出: 结构化的产品字段
    """
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="text 不能为空")
    if len(text) > 200:
        raise HTTPException(status_code=422, detail="描述不超过200字")

    # 1. 先用规则解析（无需LLM，毫秒级响应）
    parsed = _rule_parse(text)
    if parsed:
        logger.info("快速解析(规则): product={} category={}", parsed.get("product_name"), parsed.get("category"))
        return {"code": 0, "data": parsed}

    # 2. 规则失败，LLM兜底
    try:
        from app.services.llm_service import llm_service
        raw = llm_service.chat_json(
            _QUICK_PARSE_SYSTEM,
            _QUICK_PARSE_PROMPT.format(text=text),
        )
        parsed_llm = raw if isinstance(raw, dict) else {}
        cat = parsed_llm.get("category", "")
        if cat not in set(_CATEGORY_MAP.values()):
            for k, v in _CATEGORY_MAP.items():
                if k in text:
                    cat = v
                    break
            else:
                cat = "其他农产品"
        return {
            "code": 0,
            "data": {
                "product_name": parsed_llm.get("product_name", ""),
                "category": cat,
                "origin": parsed_llm.get("origin", ""),
                "price": parsed_llm.get("price", ""),
                "core_features": parsed_llm.get("core_features", ""),
            },
        }
    except Exception as exc:
        logger.error("快速解析LLM兜底也失败: {}", exc)
        raise HTTPException(status_code=500, detail="解析失败，请手动填写")


class ContentPackBody(BaseModel):
    product_name: str = Field(..., examples=["赣南脐橙"])
    category: str = Field(..., examples=["水果"])
    origin: str = Field("", examples=["江西赣州"])
    specification: str = Field("", examples=["5斤装"])
    price: str = Field("", examples=["29.9元/5斤"])
    core_features: str = Field("", examples=["高糖度，皮薄汁多"])


@router.post("/generate")
async def generate_content_pack(body: ContentPackBody):
    """
    生成今日内容包：
    - 3条抖音选题（含封面建议+拍摄角度）
    - 3条30秒口播稿（可直接念）
    - 模块化直播话术积木块
    - 今日节气营销提示
    - 推荐话题标签
    """
    logger.info("内容包请求: product={}", body.product_name)
    try:
        req = ContentPackRequest(
            product_name=body.product_name,
            category=body.category,
            origin=body.origin,
            specification=body.specification,
            price=body.price,
            core_features=body.core_features,
        )
        result = content_pack_agent.generate(req)
        result_data = {
            "product_name": result.product_name,
            "category": result.category,
            "date": result.date,
            "stages_completed": result.stages_completed,
            "stages_failed": result.stages_failed,
            "today": {
                "tip": result.today_tip,
                "season": result.season_info.get("season", ""),
                "solar_term": result.season_info.get("solar_term", ""),
                "hot_products": result.season_info.get("hot_products", []),
                "angle": result.season_info.get("angle", ""),
            },
            "topics": result.topics,
            "scripts": result.scripts,
            "live_modules": result.live_modules,
            "hashtags": result.hashtags,
            "compliance": result.compliance,
        }

        # 写库
        try:
            from app.database import async_session
            if async_session:
                async with async_session() as session:
                    record = ContentPackRecord(
                        product_name=body.product_name,
                        category=body.category,
                        origin=body.origin,
                        topics_count=len(result.topics),
                        scripts_count=len(result.scripts),
                        stages_completed=result.stages_completed,
                        request_payload={
                            "product_name": body.product_name,
                            "category": body.category,
                            "origin": body.origin,
                            "specification": body.specification,
                            "price": body.price,
                            "core_features": body.core_features,
                        },
                        result_payload=result_data,
                    )
                    session.add(record)
                    await session.commit()
        except Exception as db_exc:
            logger.warning("内容包记录写库失败: {}", db_exc)

        return {
            "code": 0,
            "message": f"内容包生成完成，已完成阶段：{', '.join(result.stages_completed)}",
            "data": result_data,
        }
    except Exception as exc:
        logger.error("内容包生成失败: {}", exc)
        raise HTTPException(status_code=500, detail=f"生成失败：{str(exc)}")


@router.get("/session")
async def get_content_pack_session():
    """兼容旧版前端：当前版本已改为浏览器本地缓存，这里返回空会话避免 500。"""
    return {
        "code": 0,
        "data": {
            "form": None,
            "result": None,
            "saved_at": "",
        },
    }


@router.post("/session/save")
async def save_content_pack_session(body: dict):
    """兼容旧版前端：保留保存接口但不强依赖数据库。"""
    return {
        "code": 0,
        "message": "会话已保存",
        "data": {
            "saved": True,
            "saved_at": body.get("saved_at", ""),
        },
    }


@router.get("/season")
async def get_season_info():
    """获取当前节气信息和时令产品推荐"""
    from datetime import datetime
    month = datetime.now().month
    info = kb.get_today_season()
    return {
        "code": 0,
        "data": {
            "month": month,
            **info,
        },
    }


@router.get("/live-modules")
async def get_live_modules():
    """获取所有直播话术积木块（未填充产品变量的原始模板）"""
    return {
        "code": 0,
        "data": kb.get_live_modules(),
    }
