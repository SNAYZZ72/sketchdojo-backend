# =============================================================================
# app/infrastructure/monitoring/health.py
# =============================================================================
import time
from typing import Any, Dict

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

health_router = APIRouter()


async def check_database_health(db: AsyncSession) -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        response_time = (time.time() - start_time) * 1000

        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and performance."""
    try:
        redis_client = redis.from_url(settings.redis_url)
        start_time = time.time()
        await redis_client.ping()
        response_time = (time.time() - start_time) * 1000
        await redis_client.close()

        return {"status": "healthy", "response_time_ms": round(response_time, 2)}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_celery_health() -> Dict[str, Any]:
    """Check Celery worker connectivity."""
    try:
        from app.core.celery_app import celery_app

        # Check if workers are active
        active_workers = celery_app.control.inspect().active()

        if active_workers:
            worker_count = len(active_workers)
            return {"status": "healthy", "active_workers": worker_count}
        else:
            return {"status": "unhealthy", "error": "No active workers found"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@health_router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "checks": {},
    }

    # Check database
    health_status["checks"]["database"] = await check_database_health(db)

    # Check Redis
    health_status["checks"]["redis"] = await check_redis_health()

    # Check Celery
    health_status["checks"]["celery"] = await check_celery_health()

    # Determine overall status
    unhealthy_services = [
        service
        for service, check in health_status["checks"].items()
        if check["status"] != "healthy"
    ]

    if unhealthy_services:
        health_status["status"] = "unhealthy"
        health_status["unhealthy_services"] = unhealthy_services

    return health_status


@health_router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe for Kubernetes."""
    try:
        # Quick database check
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not ready"}, 503


@health_router.get("/liveness")
async def liveness_check():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}
