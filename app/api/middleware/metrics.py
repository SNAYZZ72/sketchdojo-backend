# app/api/middleware/metrics.py
"""
Prometheus metrics middleware
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.monitoring.metrics import (
    active_requests,
    error_count,
    request_count,
    request_duration,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics for health checks and metrics endpoint
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Increment active requests
        active_requests.inc()

        start_time = time.time()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status_code = str(response.status_code)

            request_count.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()

            request_duration.labels(method=method, endpoint=path).observe(duration)

            # Record errors for 4xx and 5xx responses
            if response.status_code >= 400:
                error_count.labels(
                    method=method, endpoint=path, error_type="http_error"
                ).inc()

            return response

        except Exception as e:
            # Record exception metrics
            duration = time.time() - start_time

            request_count.labels(method=method, endpoint=path, status_code="500").inc()

            request_duration.labels(method=method, endpoint=path).observe(duration)

            error_count.labels(
                method=method, endpoint=path, error_type="exception"
            ).inc()

            raise
        finally:
            # Decrement active requests
            active_requests.dec()
