# =============================================================================
# app/schemas/base.py
# =============================================================================
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common fields."""

    class Config:
        from_attributes = True
        use_enum_values = True


class BaseEntitySchema(BaseSchema):
    """Base entity schema with ID and timestamps."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""

    items: list
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)
    pages: int


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    message: str
    details: Optional[dict] = None


class SuccessResponse(BaseModel):
    """Success response schema."""

    success: bool = True
    message: str
    data: Optional[dict] = None
