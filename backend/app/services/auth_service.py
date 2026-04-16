"""Auth 服务 — 注册/登录/Token校验/套餐管理"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserToken, hash_password, verify_password, generate_token

# Token 有效期（天）
TOKEN_EXPIRE_DAYS = 30

TIER_PRICE = {
    "free": 0.0,
    "basic": 498.0,
    "pro": 1280.0,
    "enterprise": 3980.0,
}

TIER_LABEL = {
    "free": "免费体验",
    "basic": "基础版",
    "pro": "专业版",
    "enterprise": "企业版",
}

# 套餐功能限额（每月）
TIER_LIMITS = {
    "free":       {"pain_point": 5,   "listing": 3,   "pipeline": 2},
    "basic":      {"pain_point": 200, "listing": 200, "pipeline": 100},
    "pro":        {"pain_point": 999, "listing": 999, "pipeline": 500},
    "enterprise": {"pain_point": 9999, "listing": 9999, "pipeline": 9999},
}


class AuthService:

    async def register(
        self, session: AsyncSession, email: str, password: str, name: str = ""
    ) -> dict:
        """注册新用户，返回 token"""
        # 检查邮箱是否已注册
        stmt = select(User).where(User.email == email.lower().strip())
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return {"ok": False, "error": "该邮箱已注册，请直接登录"}

        user = User(
            id=str(uuid.uuid4()),
            email=email.lower().strip(),
            password_hash=hash_password(password),
            name=name or email.split("@")[0],
            tier="free",
        )
        session.add(user)
        await session.flush()

        token_str = await self._create_token(session, user.id)
        await session.commit()

        logger.info("新用户注册: email={} id={}", user.email, user.id)
        return {"ok": True, "token": token_str, "user": self._user_to_dict(user)}

    async def login(
        self, session: AsyncSession, email: str, password: str
    ) -> dict:
        """登录，返回 token"""
        stmt = select(User).where(User.email == email.lower().strip())
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            return {"ok": False, "error": "邮箱或密码错误"}
        if not user.is_active:
            return {"ok": False, "error": "账号已停用，请联系客服"}

        user.last_login_at = datetime.now(timezone.utc)
        token_str = await self._create_token(session, user.id)
        await session.commit()

        logger.info("用户登录: email={}", user.email)
        return {"ok": True, "token": token_str, "user": self._user_to_dict(user)}

    async def get_user_by_token(
        self, session: AsyncSession, token: str
    ) -> Optional[User]:
        """通过 token 获取用户，无效/过期返回 None"""
        now = datetime.now(timezone.utc)
        stmt = select(UserToken).where(
            UserToken.token == token,
            UserToken.expires_at > now,
        )
        token_obj = (await session.execute(stmt)).scalar_one_or_none()
        if not token_obj:
            return None

        stmt2 = select(User).where(User.id == token_obj.user_id, User.is_active == True)
        return (await session.execute(stmt2)).scalar_one_or_none()

    async def upgrade_tier(
        self, session: AsyncSession, user_id: str, tier: str
    ) -> dict:
        """升级套餐"""
        if tier not in TIER_PRICE:
            return {"ok": False, "error": f"无效套餐: {tier}"}
        stmt = select(User).where(User.id == user_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "用户不存在"}
        user.tier = tier
        user.monthly_price = TIER_PRICE[tier]
        await session.commit()
        return {"ok": True, "user": self._user_to_dict(user)}

    async def increment_usage(
        self, session: AsyncSession, user_id: str, action: str
    ) -> bool:
        """累加使用次数，返回是否允许（未超限）"""
        stmt = select(User).where(User.id == user_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            return False

        limits = TIER_LIMITS.get(user.tier, TIER_LIMITS["free"])
        current = getattr(user, f"{action}_count", 0)
        limit = limits.get(action, 0)

        if current >= limit:
            return False

        setattr(user, f"{action}_count", current + 1)
        await session.commit()
        return True

    def check_limit(self, user: User, action: str) -> dict:
        """检查使用限额（不扣减）"""
        limits = TIER_LIMITS.get(user.tier, TIER_LIMITS["free"])
        current = getattr(user, f"{action}_count", 0)
        limit = limits.get(action, 0)
        return {
            "allowed": current < limit,
            "current": current,
            "limit": limit,
            "remaining": max(0, limit - current),
        }

    # ── 内部方法 ──────────────────────────────────────────

    async def _create_token(self, session: AsyncSession, user_id: str) -> str:
        token_str = generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
        token_obj = UserToken(token=token_str, user_id=user_id, expires_at=expires_at)
        session.add(token_obj)
        return token_str

    def _user_to_dict(self, user: User) -> dict:
        return {
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
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


auth_service = AuthService()
