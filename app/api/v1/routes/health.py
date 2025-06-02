# app/api/v1/routes/health.py
"""
Health check API routes
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import get_redis_cache
from app.infrastructure.cache.redis_cache import RedisCache

router = APIRouter()


@router.get("/")
async def health_check(settings=Depends(get_settings)):
    """Basic health check"""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "SketchDojo API",
            "version": settings.app_version,
        }
    )


@router.get("/detailed")
async def detailed_health_check(
    redis_cache: RedisCache = Depends(get_redis_cache),
    settings=Depends(get_settings),
):
    """Detailed health check including dependencies"""
    health_status = {
        "status": "healthy",
        "service": "SketchDojo API",
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {},
    }

    # Check Redis
    try:
        redis_healthy = await redis_cache.health_check()
        health_status["checks"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "details": "Redis connection test",
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "details": f"Redis error: {str(e)}",
        }
        health_status["status"] = "degraded"

    # Check AI Provider
    try:
        from app.dependencies import get_ai_provider

        ai_provider = get_ai_provider(settings)
        health_status["checks"]["ai_provider"] = {
            "status": "healthy",
            "details": f"OpenAI provider configured",
        }
    except Exception as e:
        health_status["checks"]["ai_provider"] = {
            "status": "unhealthy",
            "details": f"AI provider error: {str(e)}",
        }
        health_status["status"] = "degraded"

    # Check Image Generator
    try:
        from app.dependencies import get_image_generator

        image_gen = get_image_generator(settings)
        health_status["checks"]["image_generator"] = {
            "status": "healthy" if image_gen.is_available() else "degraded",
            "details": "Stability AI provider"
            if image_gen.is_available()
            else "Using placeholders",
        }
    except Exception as e:
        health_status["checks"]["image_generator"] = {
            "status": "unhealthy",
            "details": f"Image generator error: {str(e)}",
        }

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(health_status, status_code=status_code)
