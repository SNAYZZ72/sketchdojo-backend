# app/monitoring/metrics.py
"""
Prometheus metrics definitions
"""
from prometheus_client import Counter, Gauge, Histogram, Info

# Application info
app_info = Info("sketchdojo_app", "SketchDojo application information")

# Request metrics
request_count = Counter(
    "sketchdojo_requests_total",
    "Total number of requests",
    labelnames=["method", "endpoint", "status_code"],
)

request_duration = Histogram(
    "sketchdojo_request_duration_seconds",
    "Request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
)

active_requests = Gauge("sketchdojo_active_requests", "Number of active requests")

# Error metrics
error_count = Counter(
    "sketchdojo_errors_total",
    "Total number of errors",
    labelnames=["method", "endpoint", "error_type"],
)

# Generation metrics
generation_tasks_total = Counter(
    "sketchdojo_generation_tasks_total",
    "Total number of generation tasks",
    labelnames=["task_type", "status"],
)

generation_duration = Histogram(
    "sketchdojo_generation_duration_seconds",
    "Generation task duration in seconds",
    labelnames=["task_type"],
    buckets=[10, 30, 60, 120, 300, 600, 1200],
)

# WebSocket metrics
websocket_connections = Gauge(
    "sketchdojo_websocket_connections",
    "Number of active WebSocket connections",
)

websocket_messages = Counter(
    "sketchdojo_websocket_messages_total",
    "Total WebSocket messages",
    labelnames=["direction", "message_type"],
)

# AI provider metrics
ai_requests_total = Counter(
    "sketchdojo_ai_requests_total",
    "Total AI provider requests",
    labelnames=["provider", "model", "status"],
)

ai_request_duration = Histogram(
    "sketchdojo_ai_request_duration_seconds",
    "AI request duration in seconds",
    labelnames=["provider", "model"],
    buckets=[1, 2, 5, 10, 20, 30, 60],
)

# Image generation metrics
image_generation_total = Counter(
    "sketchdojo_image_generation_total",
    "Total image generations",
    labelnames=["provider", "style", "status"],
)

image_generation_duration = Histogram(
    "sketchdojo_image_generation_duration_seconds",
    "Image generation duration in seconds",
    labelnames=["provider", "style"],
    buckets=[5, 10, 15, 30, 45, 60, 90, 120],
)


# Storage metrics
storage_operations_total = Counter(
    "sketchdojo_storage_operations_total",
    "Total storage operations",
    labelnames=["operation", "status"],
)

storage_operation_duration = Histogram(
    "sketchdojo_storage_operation_duration_seconds",
    "Storage operation duration in seconds",
    labelnames=["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


def setup_metrics():
    """Initialize metrics with application info"""
    from app.config import get_settings

    settings = get_settings()
    app_info.info(
        {"version": settings.app_version, "environment": settings.environment}
    )


def record_ai_request(provider: str, model: str, duration: float, success: bool):
    """Record AI request metrics"""
    status = "success" if success else "error"
    ai_requests_total.labels(provider=provider, model=model, status=status).inc()
    ai_request_duration.labels(provider=provider, model=model).observe(duration)


def record_image_generation(provider: str, style: str, duration: float, success: bool):
    """Record image generation metrics"""
    status = "success" if success else "error"
    image_generation_total.labels(provider=provider, style=style, status=status).inc()
    image_generation_duration.labels(provider=provider, style=style).observe(duration)


def record_storage_operation(operation: str, duration: float, success: bool):
    """Record storage operation metrics"""
    status = "success" if success else "error"
    storage_operations_total.labels(operation=operation, status=status).inc()
    storage_operation_duration.labels(operation=operation).observe(duration)


def get_metrics():
    """Get metrics in Prometheus format"""
    from prometheus_client import generate_latest

    return generate_latest()


def get_metrics_content_type():
    """Get metrics content type"""
    from prometheus_client import CONTENT_TYPE_LATEST

    return CONTENT_TYPE_LATEST
