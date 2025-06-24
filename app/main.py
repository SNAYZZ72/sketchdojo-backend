# app/main.py
"""
FastAPI application entry point for SketchDojo backend
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from app.api.middleware.cors import setup_cors
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.metrics import MetricsMiddleware
from app.api.exception_handlers import add_exception_handlers
from app.api.v1.routes import generation, health, tasks, webtoons, test, chat
from app.config import get_settings
from app.infrastructure.notifications.redis_subscriber import create_redis_subscriber
from app.infrastructure.notifications.websocket_handlers import register_websocket_handlers
from app.monitoring.logging_config import setup_logging
from app.monitoring.metrics import get_metrics, get_metrics_content_type, setup_metrics
from app.websocket.connection_manager import get_connection_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    # Setup metrics
    if settings.enable_metrics:
        setup_metrics()

    # Initialize connection manager
    connection_manager = get_connection_manager()
    
    # Setup WebSocket tools
    try:
        from app.websocket.setup import setup_websocket_tools
        available_tools = await setup_websocket_tools()
        logger.info(f"Registered WebSocket tools: {len(available_tools)}")
    except Exception as e:
        logger.error(f"Error setting up WebSocket tools: {str(e)}")
        
    # Initialize Redis notification subscriber
    try:
        redis_subscriber = await create_redis_subscriber()
        # Register WebSocket handlers
        await register_websocket_handlers(redis_subscriber, connection_manager)
        # Start the subscriber
        await redis_subscriber.start()
        logger.info("Redis notification system initialized and running")
        app.state.redis_subscriber = redis_subscriber
    except Exception as e:
        logger.error(f"Error setting up Redis notification system: {str(e)}")

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    yield

    # Cleanup
    logger.info("Shutting down application")
    
    # Stop Redis subscriber if it exists
    if hasattr(app.state, "redis_subscriber"):
        try:
            await app.state.redis_subscriber.stop()
            logger.info("Redis notification subscriber stopped")
        except Exception as e:
            logger.error(f"Error stopping Redis subscriber: {str(e)}")
    
    # Disconnect all WebSocket clients
    await connection_manager.disconnect_all()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered webtoon creation platform",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup CORS
    setup_cors(app, settings)
    
    # Register exception handlers
    add_exception_handlers(app)

    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    if settings.enable_metrics:
        app.add_middleware(MetricsMiddleware)

    # Include API routes
    app.include_router(
        webtoons.router,
        prefix=f"{settings.api_prefix}/webtoons",
        tags=["webtoons"],
    )
    app.include_router(
        generation.router,
        prefix=f"{settings.api_prefix}/generation",
        tags=["generation"],
    )
    app.include_router(
        tasks.router, prefix=f"{settings.api_prefix}/tasks", tags=["tasks"]
    )
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(test.router, prefix=f"{settings.api_prefix}/test", tags=["test"])
    app.include_router(
        chat.router, 
        prefix=f"{settings.api_prefix}", 
        tags=["chat"]
    )

    # Metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(content=get_metrics(), media_type=get_metrics_content_type())

    # WebSocket endpoint
    from app.websocket.router import websocket_endpoint

    app.add_websocket_route("/ws", websocket_endpoint)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
