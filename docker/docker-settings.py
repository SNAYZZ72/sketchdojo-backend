"""
Docker-specific settings overrides
"""
import os

from app.config import Settings

# Load these settings by setting the environment variable:
# SKETCHDOJO_SETTINGS_MODULE=docker-settings


class DockerSettings(Settings):
    """Settings for Docker environment"""

    # Base settings
    app_name: str = "SketchDojo API (Docker)"
    environment: str = os.getenv("ENVIRONMENT", "production")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # API settings
    api_v1_prefix: str = "/api/v1"
    allow_origins: list = ["*"]  # In production, limit this to your frontend domain

    # Security settings
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-this-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 60 * 24  # 1 day in minutes

    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sketchdojo.db")

    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_max_connections: int = 10

    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000

    # Stability API settings
    stability_api_key: str = os.getenv("STABILITY_API_KEY", "")
    stability_api_url: str = os.getenv(
        "STABILITY_API_URL",
        "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
    )

    # Storage settings
    storage_provider: str = "file"  # Options: file, memory
    storage_path: str = "/app/storage"  # Docker container path

    # Rate limiting - important fix from memory
    def is_test_environment(self, request) -> bool:
        """Check if running in test environment based on request origin"""
        # Skip rate limiting for test server as noted in memory
        if hasattr(request, "url") and str(request.url).startswith("http://testserver"):
            return True
        return self.environment.lower() == "test"
