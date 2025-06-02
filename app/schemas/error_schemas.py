"""
Error response schemas
"""
from datetime import UTC, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""

    field: str
    message: str
    invalid_value: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[List[ValidationErrorDetail]] = Field(
        None, description="Validation error details"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: Optional[str] = Field(None, description="Request correlation ID")


class NotFoundResponse(ErrorResponse):
    """404 Not Found response"""

    error: str = "Resource not found"
    error_code: str = "NOT_FOUND"


class ValidationErrorResponse(ErrorResponse):
    """422 Validation Error response"""

    error: str = "Validation failed"
    error_code: str = "VALIDATION_ERROR"
    details: List[ValidationErrorDetail]


class RateLimitErrorResponse(ErrorResponse):
    """429 Rate Limit Error response"""

    error: str = "Rate limit exceeded"
    error_code: str = "RATE_LIMIT_EXCEEDED"
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")


class InternalServerErrorResponse(ErrorResponse):
    """500 Internal Server Error response"""

    error: str = "Internal server error"
    error_code: str = "INTERNAL_ERROR"
