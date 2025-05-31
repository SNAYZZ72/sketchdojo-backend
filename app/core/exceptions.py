# =============================================================================
# app/core/exceptions.py
# =============================================================================
"""
Custom exception classes for SketchDojo Backend
"""
from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class SketchDojoException(Exception):
    """Base exception for SketchDojo application."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SketchDojoException):
    """Raised when data validation fails."""

    pass


class AuthenticationError(SketchDojoException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(SketchDojoException):
    """Raised when authorization fails."""

    pass


class ResourceNotFoundError(SketchDojoException):
    """Raised when a requested resource is not found."""

    pass


class ResourceConflictError(SketchDojoException):
    """Raised when a resource conflict occurs."""

    pass


class BusinessLogicError(SketchDojoException):
    """Raised when business logic constraints are violated."""

    pass


class ExternalServiceError(SketchDojoException):
    """Raised when external service calls fail."""

    pass


class AIServiceError(ExternalServiceError):
    """Raised when AI service calls fail."""

    pass


class StorageError(SketchDojoException):
    """Raised when storage operations fail."""

    pass


class TaskError(SketchDojoException):
    """Raised when background task operations fail."""

    pass


class RateLimitError(SketchDojoException):
    """Raised when rate limits are exceeded."""

    pass


class QuotaExceededError(SketchDojoException):
    """Raised when user quotas are exceeded."""

    pass


# HTTP Exception mappers
def map_to_http_exception(exc: SketchDojoException) -> HTTPException:
    """Map domain exceptions to HTTP exceptions."""

    if isinstance(exc, ValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)

    elif isinstance(exc, AuthenticationError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    elif isinstance(exc, AuthorizationError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

    elif isinstance(exc, ResourceNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

    elif isinstance(exc, ResourceConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)

    elif isinstance(exc, RateLimitError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)

    elif isinstance(exc, QuotaExceededError):
        return HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=exc.message)

    elif isinstance(exc, (ExternalServiceError, AIServiceError)):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="External service unavailable"
        )

    elif isinstance(exc, (StorageError, TaskError)):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal service error"
        )

    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )
