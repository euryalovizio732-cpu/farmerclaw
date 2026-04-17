"""数据库连接与会话管理 — SQLite（开发）/ PostgreSQL（生产）均支持"""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()
DATABASE_URL = ""

db_available = False
engine = None
async_session = None


class Base(DeclarativeBase):
    pass


def _normalize_database_url(database_url: str) -> str:
    normalized = (database_url or "").strip()
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://"):]
    if normalized.startswith("postgresql+psycopg2://"):
        normalized = "postgresql+asyncpg://" + normalized[len("postgresql+psycopg2://"):]
    elif normalized.startswith("postgresql://"):
        normalized = "postgresql+asyncpg://" + normalized[len("postgresql://"):]
    if normalized.startswith("postgresql+asyncpg://"):
        parsed = urlsplit(normalized)
        query_items = []
        changed = False
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key == "sslmode":
                key = "ssl"
                changed = True
            query_items.append((key, value))
        if changed:
            normalized = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query_items), parsed.fragment))
    return normalized


DATABASE_URL = _normalize_database_url(settings.database_url)


async def _patch_sqlite_schema():
    if engine is None or "sqlite" not in DATABASE_URL:
        return
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(content_pack_records)"))
            columns = {row[1] for row in result.fetchall()}
            if "request_payload" not in columns:
                await conn.execute(text("ALTER TABLE content_pack_records ADD COLUMN request_payload JSON DEFAULT '{}'"))
            if "result_payload" not in columns:
                await conn.execute(text("ALTER TABLE content_pack_records ADD COLUMN result_payload JSON DEFAULT '{}'"))
    except Exception as exc:
        logger.warning("SQLite 内容包表结构补丁失败: {}", exc)


def _init_engine():
    global engine, async_session
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

        connect_args = {}
        if "supabase.co" in settings.database_url or "sslmode=require" in settings.database_url:
            connect_args = {"ssl": True}

        kwargs: dict = {"echo": settings.app_debug, "pool_pre_ping": True, "pool_size": 10, "max_overflow": 20, "connect_args": connect_args}
        if "sqlite" in DATABASE_URL:
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["pool_size"] = 10
            kwargs["max_overflow"] = 5

        engine = create_async_engine(DATABASE_URL, **kwargs)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        return True
    except Exception as exc:
        logger.warning("无法创建数据库引擎: {}", exc)
        return False


async def get_db():
    if async_session is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="数据库未连接，该功能暂不可用")
    from sqlalchemy.ext.asyncio import AsyncSession
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    global db_available
    if not _init_engine():
        logger.warning("数据库引擎不可用 — 以无DB模式运行")
        return False
    try:
        import app.models  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _patch_sqlite_schema()
        db_available = True
        logger.info("数据库初始化成功")
        return True
    except Exception as exc:
        logger.warning("数据库连接失败: {} — 以无DB模式运行", exc)
        db_available = False
        return False
