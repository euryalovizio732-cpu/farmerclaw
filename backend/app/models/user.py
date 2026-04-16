"""用户数据模型"""

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(60), nullable=False, default="")

    # 套餐：free / basic(498) / pro(1280) / enterprise(3980)
    tier = Column(String(20), nullable=False, default="free")
    monthly_price = Column(Float, default=0.0)

    # 使用统计
    pain_point_count = Column(Integer, default=0)
    listing_count = Column(Integer, default=0)
    pipeline_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = Column(DateTime, nullable=True)


class UserToken(Base):
    __tablename__ = "user_tokens"

    token = Column(String(64), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, h = password_hash.split(":", 1)
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == h
    except Exception:
        return False


def generate_token() -> str:
    return secrets.token_hex(32)
