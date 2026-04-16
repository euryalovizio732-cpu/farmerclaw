"""账号认证 — API 路由"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from loguru import logger

from app.database import get_db
from app.services.auth_service import auth_service, TIER_PRICE, TIER_LABEL, TIER_LIMITS

router = APIRouter(prefix="/api/auth", tags=["账号认证"])


# ── 请求/响应模型 ──────────────────────────────────────

class RegisterBody(BaseModel):
    email: str = Field(..., description="邮箱", examples=["farmer@example.com"])
    password: str = Field(..., min_length=6, description="密码（至少6位）")
    name: str = Field("", description="姓名/昵称")


class LoginBody(BaseModel):
    email: str
    password: str


class UpgradeBody(BaseModel):
    tier: str = Field(..., description="套餐档位: basic/pro/enterprise")


# ── 依赖：从 Header 提取当前用户 ──────────────────────

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.split(" ", 1)[1]
    user = await auth_service.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db=Depends(get_db),
):
    """可选认证，未登录返回 None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    return await auth_service.get_user_by_token(db, token)


# ── 路由 ──────────────────────────────────────────────

@router.post("/register")
async def register(body: RegisterBody, db=Depends(get_db)):
    """用户注册"""
    result = await auth_service.register(db, body.email, body.password, body.name)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"code": 0, "message": "注册成功", "data": result}


@router.post("/login")
async def login(body: LoginBody, db=Depends(get_db)):
    """用户登录"""
    result = await auth_service.login(db, body.email, body.password)
    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {"code": 0, "message": "登录成功", "data": result}


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    """获取当前用户信息"""
    from app.services.auth_service import TIER_LIMITS, TIER_LABEL
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tier": user.tier,
            "tier_label": TIER_LABEL.get(user.tier, user.tier),
            "monthly_price": user.monthly_price,
            "pain_point_count": user.pain_point_count,
            "listing_count": user.listing_count,
            "pipeline_count": user.pipeline_count,
            "limits": TIER_LIMITS.get(user.tier, TIER_LIMITS["free"]),
        },
    }


@router.post("/upgrade")
async def upgrade_tier(body: UpgradeBody, user=Depends(get_current_user), db=Depends(get_db)):
    """升级套餐（内测阶段直接升级，无需支付校验）"""
    result = await auth_service.upgrade_tier(db, user.id, body.tier)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"code": 0, "message": "套餐升级成功", "data": result}


@router.get("/tiers")
async def get_tiers():
    """获取套餐列表"""
    return {
        "code": 0,
        "data": [
            {
                "tier": tier,
                "label": TIER_LABEL[tier],
                "price": TIER_PRICE[tier],
                "limits": TIER_LIMITS[tier],
                "features": _tier_features(tier),
            }
            for tier in ["free", "basic", "pro", "enterprise"]
        ],
    }


def _tier_features(tier: str) -> list[str]:
    features = {
        "free": ["痛点分析5次/月", "Listing生成3次/月", "全流程分析2次/月", "基础合规检测"],
        "basic": ["痛点分析200次/月", "Listing生成200次/月", "全流程分析100次/月", "合规校验+自动修复", "抖音/拼多多适配"],
        "pro": ["不限次数使用", "投放优化Agent（即将上线）", "评价维护Agent（即将上线）", "优先客服支持", "多平台适配"],
        "enterprise": ["全部专业版功能", "多店铺管理", "专属运营顾问", "1v1陪跑服务", "定制化开发"],
    }
    return features.get(tier, [])
