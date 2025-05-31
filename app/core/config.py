"""
Core configuration for SketchDojo Backend
File: app/core/config.py
"""
import os
import secrets
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.security import SecuritySettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Environment type
    environment: str = "development"

    # Application
    app_name: str = "SketchDojo Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    # Load secret key from environment variable with a fallback for development
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

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

    # Security Configuration
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    # Enhanced CORS validation
    @field_validator("cors_origins", mode="before")
    def validate_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            origins = v if isinstance(v, list) else [v]
        else:
            raise ValueError("Invalid CORS origins format")

        # Security check: warn about wildcard in production
        if "*" in origins and os.getenv("ENVIRONMENT") == "production":
            logger.warning("Wildcard CORS origin detected in production environment")

        return origins

    # Database URL validation with security checks
    @field_validator("database_url", mode="before")
    def validate_database_url_security(cls, v):
        if not v.startswith(("mysql+", "postgresql+", "sqlite+")):
            raise ValueError("database_url must specify a valid database driver")

        # Security check: warn about default credentials
        if "password@" in v or "root:root@" in v or "admin:admin@" in v:
            logger.warning("Default database credentials detected - change in production")

        return v

    # Redis URL validation
    @field_validator("redis_url", mode="before")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://") and not v.startswith("rediss://"):
            raise ValueError("redis_url must be a valid Redis URL")
        return v

    # API key validation
    @field_validator("openai_api_key", "anthropic_api_key", "stability_ai_api_key", mode="before")
    def validate_api_keys(cls, v):
        if v and len(v) < 10:
            raise ValueError("API key appears to be too short")
        return v

    def get_cors_config(self) -> dict:
        """Get CORS configuration."""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.security.cors_allow_credentials,
            "allow_methods": self.security.cors_allow_methods,
            "allow_headers": self.security.cors_allow_headers,
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def get_jwt_config(self) -> dict:
        """Get JWT configuration."""
        return {
            "secret_key": self.secret_key,
            "algorithm": self.security.algorithm,
            "access_token_expire_minutes": self.security.access_token_expire_minutes,
            "refresh_token_expire_days": self.security.refresh_token_expire_days,
        }


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
