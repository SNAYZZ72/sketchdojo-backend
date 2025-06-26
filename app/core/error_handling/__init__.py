"""
Error handling package for the application.

This package contains custom exceptions and error handling utilities.
"""

from .base_error_handler import BaseErrorHandler
from .errors import (
    AppError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    RateLimitError,
    ServiceUnavailableError,
    BadGatewayError,
    GatewayTimeoutError
)

__all__ = [
    'BaseErrorHandler',
    'AppError',
    'ValidationError',
    'NotFoundError',
    'UnauthorizedError',
    'ForbiddenError',
    'ConflictError',
    'RateLimitError',
    'ServiceUnavailableError',
    'BadGatewayError',
    'GatewayTimeoutError',
]
