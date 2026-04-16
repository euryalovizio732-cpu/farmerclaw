"""样本库管理 — API 路由
查看/添加/导入/审核样本，供管理后台使用。
"""

import json
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel, Field
from loguru import logger

from app.services.sample_library import (
    SAMPLES, _VALIDATED_SAMPLES, add_validated_sample, get_sample_stats,
)

router = APIRouter(prefix="/api/samples", tags=["样本库"])


# ─── 查看样本 ───

@router.get("/stats")
async def sample_stats():
    """样本库总体统计"""
    return {"code": 0, "data": get_sample_stats()}


@router.get("/list")
async def list_samples(category: str = "", sample_type: str = "script"):
    """列出指定品类的样本"""
    results = []

    # 基础样本
    if category:
        cat_data = SAMPLES.get(category, {})
        items = cat_data.get(sample_type, [])
        for i, s in enumerate(items):
            results.append({**s, "id": f"base_{category}_{sample_type}_{i}", "source_type": "base", "category": category})
    else:
        for cat, types in SAMPLES.items():
            items = types.get(sample_type, [])
            for i, s in enumerate(items):
                results.append({**s, "id": f"base_{cat}_{sample_type}_{i}", "source_type": "base", "category": cat})

    # 验证样本
    if category:
        for i, s in enumerate(_VALIDATED_SAMPLES.get(category, [])):
            results.append({**s, "id": f"val_{category}_{i}", "source_type": "validated", "category": category})
    else:
        for cat, items in _VALIDATED_SAMPLES.items():
            for i, s in enumerate(items):
                results.append({**s, "id": f"val_{cat}_{i}", "source_type": "validated", "category": cat})

    return {
        "code": 0,
        "data": {
            "total": len(results),
            "samples": results,
        },
    }


@router.get("/categories")
async def list_categories():
    """返回所有品类列表"""
    cats = list(SAMPLES.keys())
    return {"code": 0, "data": cats}


# ─── 添加样本 ───

class AddSampleBody(BaseModel):
    category: str = Field(..., examples=["脐橙"])
    sample_type: str = Field("script", examples=["script"])
    script: str = Field("", description="口播文本/选题标题/话术文本")
    title: str = Field("", description="选题标题（topic类型时使用）")
    text: str = Field("", description="通用文本字段")
    hook_type: str = Field("", examples=["价格冲击"])
    source: str = Field("manual", examples=["抖音@xxx"])
    views_approx: int = Field(0)
    usable_direct: bool = Field(False)


@router.post("/add")
async def add_sample(body: AddSampleBody):
    """手动添加单条样本"""
    cat = body.category
    stype = body.sample_type

    if cat not in SAMPLES:
        SAMPLES[cat] = {"script": [], "topic": [], "live_module": [], "pain_point": [], "reply": []}

    if stype not in SAMPLES[cat]:
        SAMPLES[cat][stype] = []

    content = body.script or body.title or body.text
    if not content:
        return {"code": -1, "message": "内容不能为空"}

    sample = {
        "script": content,
        "hook_type": body.hook_type or "待分类",
        "source": body.source,
        "views_approx": body.views_approx,
        "usable_direct": body.usable_direct,
    }

    SAMPLES[cat][stype].append(sample)
    logger.info("手动添加样本: category={} type={} len={}", cat, stype, len(content))

    return {"code": 0, "message": f"已添加到 {cat}/{stype}，当前共 {len(SAMPLES[cat][stype])} 条"}


# ─── 批量导入 JSON ───

@router.post("/import")
async def import_samples(
    file: UploadFile = File(...),
    category: str = Form(...),
    sample_type: str = Form("script"),
):
    """从 JSON 文件批量导入样本"""
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))

        if not isinstance(data, list):
            return {"code": -1, "message": "JSON 应为数组格式"}

        if category not in SAMPLES:
            SAMPLES[category] = {"script": [], "topic": [], "live_module": [], "pain_point": [], "reply": []}
        if sample_type not in SAMPLES[category]:
            SAMPLES[category][sample_type] = []

        added = 0
        for item in data:
            text = item.get("script", "") or item.get("desc", "") or item.get("title", "") or item.get("text", "")
            if not text or len(text) < 10:
                continue

            sample = {
                "script": text,
                "hook_type": item.get("hook_type", "待分类"),
                "source": item.get("source", item.get("author", "导入")),
                "views_approx": int(item.get("views_approx", item.get("digg", 0)) or 0),
                "usable_direct": item.get("usable_direct", False),
            }
            SAMPLES[category][sample_type].append(sample)
            added += 1

        logger.info("批量导入: category={} type={} added={}/{}", category, sample_type, added, len(data))
        return {
            "code": 0,
            "message": f"成功导入 {added} 条样本到 {category}/{sample_type}",
            "data": {"added": added, "total_in_category": len(SAMPLES[category][sample_type])},
        }

    except json.JSONDecodeError:
        return {"code": -1, "message": "JSON 格式错误"}
    except Exception as e:
        logger.error("导入失败: {}", e)
        return {"code": -1, "message": f"导入失败: {str(e)}"}


# ─── 审核/验证样本 ───

class ValidateSampleBody(BaseModel):
    category: str
    sample_type: str = "script"
    index: int = Field(..., description="样本在该品类/类型列表中的索引")
    usable_direct: bool = True


@router.post("/validate")
async def validate_sample(body: ValidateSampleBody):
    """标记样本为已验证/直接可用"""
    cat_data = SAMPLES.get(body.category, {})
    items = cat_data.get(body.sample_type, [])

    if body.index < 0 or body.index >= len(items):
        return {"code": -1, "message": "索引超出范围"}

    items[body.index]["usable_direct"] = body.usable_direct
    logger.info("样本验证: category={} index={} usable={}", body.category, body.index, body.usable_direct)

    return {"code": 0, "message": "已更新验证状态"}
