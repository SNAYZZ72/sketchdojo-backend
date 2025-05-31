"""
Core configuration for SketchDojo Backend
File: app/core/config.py
"""
import os
import secrets
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Environment type
    environment: str = "development"

    # Application
    app_name: str = "SketchDojo Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = secrets.token_urlsafe(32)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Database
    database_url: str = "mysql+asyncmy://user:password@localhost:3306/sketchdojo"
    database_pool_size: int = 20
    database_max_overflow: int = 50
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600  # 1 hour default TTL

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True

    # AI Services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    stability_ai_api_key: Optional[str] = None

    # AI Configuration
    default_llm_model: str = "gpt-4o-mini"
    default_image_model: str = "stable-diffusion-xl-1024-v1-0"
    max_panels_per_webtoon: int = 20
    max_characters_per_webtoon: int = 10

    # File Storage
    storage_type: str = "local"  # local, s3
    local_storage_path: str = "./storage"
    s3_bucket_name: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None

    # Security
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # WebSocket
    websocket_ping_interval: int = 10
    websocket_ping_timeout: int = 5

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"

    # Task Processing
    max_concurrent_tasks_per_user: int = 3
    task_timeout_seconds: int = 600
    cleanup_interval_hours: int = 24

    @field_validator("cors_origins", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("database_url", mode="before")
    def validate_database_url(cls, v):
        if not v.startswith(("mysql+", "postgresql+", "sqlite+")):
            raise ValueError("database_url must specify a valid database driver")
        return v


class DevelopmentSettings(Settings):
    """Development environment settings."""

    debug: bool = True
    database_echo: bool = True
    log_level: str = "DEBUG"
    # Explicitly override the CORS_ORIGINS to allow all origins in development
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]


class ProductionSettings(Settings):
    """Production environment settings."""

    debug: bool = False
    database_echo: bool = False
    log_level: str = "WARNING"
    enable_metrics: bool = True


class TestSettings(Settings):
    """Test environment settings."""

    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/15"  # Use different DB for tests
    celery_task_always_eager: bool = True  # Run tasks synchronously in tests


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionSettings(environment="production")
    elif env == "test":
        return TestSettings(environment="test")
    else:
        return DevelopmentSettings(environment="development")


# Global settings instance
settings = get_settings()
