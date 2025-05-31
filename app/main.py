# =============================================================================
# app/main.py
# =============================================================================
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.logging import setup_logging
from app.core.middleware import LoggingMiddleware, RateLimitMiddleware
from app.infrastructure.monitoring.health import health_router
from app.core.security import SecurityMiddleware, SecuritySettings


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting SketchDojo Backend")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down SketchDojo Backend")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Add security middleware
security_settings = SecuritySettings()
app.add_middleware(SecurityMiddleware, settings=security_settings)

# Include routers
app.include_router(api_router)
app.include_router(health_router, prefix="/health", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to SketchDojo Backend",
        "version": settings.app_version,
        "docs_url": "/docs" if settings.debug else None,
    }
