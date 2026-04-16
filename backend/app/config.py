"""FarmerClaw 配置管理 — 三农电商AI Agent平台"""

from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FARMER_",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用基础
    app_name: str = "FarmerClaw"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = Field(8001, validation_alias=AliasChoices("FARMER_APP_PORT", "PORT"))
    app_debug: bool = True

    # 数据库
    database_url: str = Field(
        "sqlite+aiosqlite:///./farmerclaw.db",
        validation_alias=AliasChoices("FARMER_DATABASE_URL", "DATABASE_URL"),
    )

    # LLM — DashScope (通义千问) 或 OpenAI-compatible
    dashscope_api_key: str = Field(
        "",
        validation_alias=AliasChoices("FARMER_DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY"),
    )
    llm_model: str = "qwen-plus"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # CORS
    cors_origins: str = Field(
        "http://localhost:5200,http://127.0.0.1:5200,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        validation_alias=AliasChoices("FARMER_CORS_ORIGINS", "CORS_ORIGINS"),
    )

    # 限流（每分钟/每天）
    rate_limit_per_minute: int = 30
    rate_limit_per_day: int = 500

    # 平台
    default_platform: str = "douyin"  # douyin | pinduoduo | huinong


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
