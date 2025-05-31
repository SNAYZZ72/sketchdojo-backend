# =============================================================================
# app/infrastructure/monitoring/metrics.py
# =============================================================================
import logging
import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)

# Create custom registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

active_connections = Gauge(
    "websocket_connections_active", "Active WebSocket connections", registry=registry
)

task_count = Counter(
    "celery_tasks_total", "Total Celery tasks", ["task_type", "status"], registry=registry
)

task_duration = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_type"],
    registry=registry,
)

ai_generation_count = Counter(
    "ai_generations_total",
    "Total AI generations",
    ["generation_type", "model", "status"],
    registry=registry,
)

ai_generation_duration = Histogram(
    "ai_generation_duration_seconds",
    "AI generation duration in seconds",
    ["generation_type", "model"],
    registry=registry,
)

database_connections = Gauge(
    "database_connections_active", "Active database connections", registry=registry
)


class MetricsMiddleware:
    """Middleware to collect HTTP request metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        start_time = time.time()

        # Track request
        method = request.method
        path = request.url.path

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time

                # Record metrics
                request_count.labels(method=method, endpoint=path, status_code=status_code).inc()

                request_duration.labels(method=method, endpoint=path).observe(duration)

            await send(message)

        await self.app(scope, receive, send_wrapper)


def record_task_metric(task_type: str, status: str, duration: float = None):
    """Record Celery task metrics."""
    task_count.labels(task_type=task_type, status=status).inc()

    if duration is not None:
        task_duration.labels(task_type=task_type).observe(duration)


def record_ai_generation_metric(
    generation_type: str, model: str, status: str, duration: float = None
):
    """Record AI generation metrics."""
    ai_generation_count.labels(generation_type=generation_type, model=model, status=status).inc()

    if duration is not None:
        ai_generation_duration.labels(generation_type=generation_type, model=model).observe(
            duration
        )


def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest(registry)
