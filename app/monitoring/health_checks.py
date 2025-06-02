# app/monitoring/health_checks.py
"""
Health check implementations
"""
import logging
from typing import Any, Dict, Optional

import redis.asyncio as redis
from sqlalchemy import text

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check coordinator"""

    def __init__(self):
        self.checks = {}

    def register_check(self, name: str, check_func):
        """Register a health check function"""
        self.checks[name] = check_func

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_status = "healthy"

        for name, check_func in self.checks.items():
            try:
                result = await check_func()
                results[name] = result

                if result.get("status") != "healthy":
                    overall_status = "degraded"

            except Exception as e:
                logger.error(f"Health check {name} failed: {str(e)}")
                results[name] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"

        return {"status": overall_status, "checks": results}


async def check_redis_health(redis_client: redis.Redis) -> Dict[str, Any]:
    """Check Redis connection health"""
    try:
        await redis_client.ping()
        return {"status": "healthy", "details": "Redis connection successful"}
    except Exception as e:
        return {"status": "unhealthy", "details": f"Redis connection failed: {str(e)}"}


async def check_ai_provider_health() -> Dict[str, Any]:
    """Check AI provider health"""
    try:
        from app.dependencies import get_ai_provider

        # This is a simple check - in production, you might want to make a test request
        ai_provider = get_ai_provider()

        return {"status": "healthy", "details": "AI provider configured"}
    except Exception as e:
        return {"status": "unhealthy", "details": f"AI provider error: {str(e)}"}


async def check_image_generator_health() -> Dict[str, Any]:
    """Check image generator health"""
    try:
        from app.dependencies import get_image_generator

        image_gen = get_image_generator()

        if image_gen.is_available():
            return {"status": "healthy", "details": "Image generator available"}
        else:
            return {
                "status": "degraded",
                "details": "Image generator not available, using placeholders",
            }
    except Exception as e:
        return {"status": "unhealthy", "details": f"Image generator error: {str(e)}"}
