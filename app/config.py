# app/config.py
"""
Configuration management for SketchDojo backend
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Define the model config with env var prefixes and env file settings
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = Field(default="SketchDojo API")
    app_version: str = Field(default="2.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")

    # Security
    secret_key: str
    cors_origins: tuple[str, ...] = Field(default=("*",))

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = Field(default=20)

    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # AI Provider Configuration
    openai_api_key: str
    openai_model: str = Field(default="gpt-4o-mini")
    openai_temperature: float = Field(default=0.7)
    openai_max_tokens: int = Field(default=4000)

    # Image Generation Configuration
    stability_api_key: Optional[str] = Field(default=None)
    stability_api_url: str = Field(
        default="https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    )

    # Storage Configuration
    storage_type: str = Field(default="memory")  # memory, file
    file_storage_path: str = Field(default="./storage")

    # Generation Configuration
    max_panels_per_webtoon: int = Field(default=20)
    default_image_width: int = Field(default=1024)
    default_image_height: int = Field(default=1024)
    generation_timeout: int = Field(default=300)  # seconds

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)
    log_level: str = Field(default="INFO")

    # WebSocket Configuration
    websocket_heartbeat_interval: int = Field(default=30)
    websocket_max_connections: int = Field(default=100)

    # Define model_config with all settings in one place
    model_config = SettingsConfigDict(
        # Removed env_file to prevent DotEnvSettingsSource from being used
        case_sensitive=False,
        extra="allow",
        frozen=True,
    )

    @field_validator("cors_origins", mode="before")
    def validate_cors_origins(cls, v):
        """Convert any list to tuple for hashability, or string to list then tuple"""
        if isinstance(v, list):
            return tuple(v)
        elif isinstance(v, str):
            # Handle comma-separated string like "http://localhost:3000,http://example.com"
            if ',' in v:
                return tuple(origin.strip() for origin in v.split(','))
            # Handle JSON-formatted string array like '["http://localhost:3000"]'
            elif v.startswith('[') and v.endswith(']'):
                try:
                    import json
                    origins = json.loads(v)
                    if isinstance(origins, list):
                        return tuple(origins)
                except (json.JSONDecodeError, TypeError):
                    pass
            # Single origin as string
            return (v,)
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
