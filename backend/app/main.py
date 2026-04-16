"""FarmerClaw Backend — 三农电商AI Agent 平台入口

启动方式：
  uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger

from app.config import get_settings
from app.db.session import engine
from app.db.base import Base

settings = get_settings()

# Create tables on startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")

raw_cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
allow_all_origins = "*" in raw_cors_origins
cors_origins = [origin for origin in raw_cors_origins if origin != "*"]

app = FastAPI(
    title="FarmerClaw API",
    description="三农短视频卖点挖掘与口播稿生成系统",
    version="0.1.0",
)

# Vercel needs the app variable to be accessible
# No changes to the actual FastAPI logic below

app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if allow_all_origins else cors_origins,
    allow_origin_regex=".*" if allow_all_origins else None,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 全局异常处理 ──

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("[Validation] path={} errors={}", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"code": -2, "message": "请求参数有误，请检查输入内容", "data": None},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning("[HTTP] status={} path={}", exc.status_code, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail or "请求处理失败", "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("[Unhandled] path={} exc={!r}", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"code": -1, "message": "服务内部错误，请稍后重试", "data": None},
    )


# ── 生命周期 ──

@app.on_event("startup")
async def startup():
    logger.info("FarmerClaw 启动中...")
    try:
        from app.database import init_db
        await init_db()
    except Exception as exc:
        logger.warning("数据库初始化失败（无DB模式运行）: {}", exc)
    logger.info("FarmerClaw 启动完成 ✅  端口: {}", settings.app_port)


@app.on_event("shutdown")
async def shutdown():
    logger.info("FarmerClaw 关闭中...")


# ── 健康检查 ──

@app.get("/health", tags=["ops"])
async def health():
    return {"status": "healthy", "service": "farmerclaw-backend", "version": settings.app_version}


@app.get("/health/ready", tags=["ops"])
async def ready():
    checks: dict = {}
    try:
        from app.services.compliance_engine import compliance_engine
        compliance_engine.check("测试", "标题")
        checks["compliance_engine"] = "ok"
    except Exception as exc:
        checks["compliance_engine"] = f"error: {exc}"

    try:
        from app.services.knowledge_base import kb
        kb.get_all_categories()
        checks["knowledge_base"] = "ok"
    except Exception as exc:
        checks["knowledge_base"] = f"error: {exc}"

    try:
        from app.database import db_available
        checks["database"] = "ok" if db_available else "unavailable"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    all_ok = all(v in ("ok", "unavailable") for v in checks.values())
    return JSONResponse(
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
        status_code=200 if all_ok else 503,
    )


# ── 路由注册 ──

# API Routers for Vercel mapping
from app.api.topic import router as topic_router
from app.api.listing import router as listing_router
from app.api.pain_point import router as pain_point_router
from app.api.reply import router as reply_router
from app.api.content_pack import router as content_pack_router

# Core API routes
app.include_router(topic_router, prefix="/api/topic", tags=["topic"])
app.include_router(listing_router, prefix="/api/listing", tags=["listing"])
app.include_router(pain_point_router, prefix="/api/pain-point", tags=["pain-point"])
app.include_router(reply_router, prefix="/api/reply", tags=["reply"])
app.include_router(content_pack_router, prefix="/api/content-pack", tags=["content-pack"])

# Health Check with /api prefix for Vercel
@app.get("/api/health/ready", tags=["ops"])
async def api_health_ready():
    return {"status": "ready"}

@app.get("/", tags=["ops"])
async def root():
    return {
        "service": "FarmerClaw — 三农电商AI Agent",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "modules": {
            "痛点挖掘Agent": "/api/pain-point/analyze",
            "Listing生成Agent": "/api/listing/generate",
            "合规检测": "/api/listing/compliance-check",
            "数据看板": "/api/dashboard/stats",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
