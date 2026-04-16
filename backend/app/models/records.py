"""FarmerClaw ORM 模型 — 痛点报告 & Listing记录 & 内容包记录"""

import datetime
from sqlalchemy import String, Text, Integer, DateTime, JSON, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PainPointRecord(Base):
    __tablename__ = "pain_point_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    product_name: Mapped[str] = mapped_column(String(200))
    platform: Mapped[str] = mapped_column(String(50), default="douyin")
    pain_points: Mapped[dict] = mapped_column(JSON, default=dict)
    opportunities: Mapped[str] = mapped_column(Text, default="")
    pricing_suggestion: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class ListingRecord(Base):
    __tablename__ = "listing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), index=True)
    platform: Mapped[str] = mapped_column(String(50), default="douyin")
    title: Mapped[str] = mapped_column(String(500))
    selling_points: Mapped[dict] = mapped_column(JSON, default=dict)
    detail_page: Mapped[str] = mapped_column(Text, default="")
    video_script: Mapped[str] = mapped_column(Text, default="")
    live_script: Mapped[str] = mapped_column(Text, default="")
    compliance_passed: Mapped[bool] = mapped_column(default=True)
    compliance_issues: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class FeedbackRecord(Base):
    """用户对生成内容的可用性反馈（核心迭代数据）"""
    __tablename__ = "feedback_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_type: Mapped[str] = mapped_column(String(50))       # script/topic/live_module/reply
    content_id: Mapped[str] = mapped_column(String(100), default="")
    product_name: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    rating: Mapped[str] = mapped_column(String(20))             # usable / needs_edit / unusable
    edited_text: Mapped[str] = mapped_column(Text, default="")  # 商家改了什么（最宝贵数据）
    comment: Mapped[str] = mapped_column(Text, default="")      # 简短反馈
    user_id: Mapped[str] = mapped_column(String(36), default="anonymous", index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class ContentPackRecord(Base):
    __tablename__ = "content_pack_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True, default="anonymous")
    product_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), index=True)
    origin: Mapped[str] = mapped_column(String(100), default="")
    topics_count: Mapped[int] = mapped_column(Integer, default=0)
    scripts_count: Mapped[int] = mapped_column(Integer, default=0)
    stages_completed: Mapped[dict] = mapped_column(JSON, default=list)
    request_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
