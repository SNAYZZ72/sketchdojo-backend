# app/schemas/common_schemas.py
"""
Common schemas used across multiple endpoints
"""
from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Mixin for entities with timestamps"""

    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseModel):
    """Base paginated response"""

    page: int
    size: int
    total: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Standard error response"""

    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SuccessResponse(BaseModel):
    """Standard success response"""

    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
