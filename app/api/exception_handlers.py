"""
Exception handlers for the API layer
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Type, Union

from app.utils.exceptions import (
    SketchDojoException as DomainException,
    EntityNotFoundError as EntityNotFoundException,
    ValidationError as ValidationException
)

# If this is needed, define it here since it doesn't exist
class PermissionDeniedException(DomainException):
    """Raised when a user lacks permission for an action"""
    pass


class APIException(Exception):
    """Base exception for API layer"""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: Optional[str] = None, status_code: Optional[int] = None):
        if detail:
            self.detail = detail
        if status_code:
            self.status_code = status_code
        super().__init__(self.detail)


class NotFoundException(APIException):
    """Resource not found exception"""
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class BadRequestException(APIException):
    """Bad request exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad request"


class UnauthorizedException(APIException):
    """Unauthorized exception"""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Unauthorized"


class ForbiddenException(APIException):
    """Forbidden exception"""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Forbidden"


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to the application"""
    
    # API Exceptions
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # Domain Exceptions
    @app.exception_handler(EntityNotFoundException)
    async def entity_not_found_exception_handler(
        request: Request, exc: EntityNotFoundException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(
        request: Request, exc: ValidationException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(PermissionDeniedException)
    async def permission_denied_exception_handler(
        request: Request, exc: PermissionDeniedException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(DomainException)
    async def domain_exception_handler(
        request: Request, exc: DomainException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )
        
    # Generic exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # In production, we'd want to log this exception
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"}
        )
