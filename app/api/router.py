# =============================================================================
# app/api/router.py
# =============================================================================
from fastapi import APIRouter

from app.api.v1.router import router as v1_router
from app.core.config import settings

api_router = APIRouter()
# Use settings.api_v1_prefix as the single source of truth for API prefix
api_router.include_router(v1_router, prefix=settings.api_v1_prefix)
