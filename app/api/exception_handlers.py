"""
Exception handlers for the API layer
"""
from datetime import datetime, UTC
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict, Optional, Type, Union

from app.core.error_handling.errors import (
    AppError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    BadRequestError,
    InternalServerError
)
from app.schemas.error_schemas import ErrorResponse
from pydantic import ValidationError as PydanticValidationError

async def create_error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Any] = None,
) -> JSONResponse:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
        
    Returns:
        JSONResponse with standardized error format
    """
    error_response = ErrorResponse(
        error=message,
        error_code=error_code or f"HTTP_{status_code}",
        timestamp=datetime.now(UTC).isoformat(),
        details=details
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True)
    )

def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to the application"""
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle application-specific errors"""
        return await create_error_response(
            status_code=exc.status_code,
            message=str(exc),
            error_code=exc.error_code,
            details=exc.details
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors"""
        return await create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Validation error",
            error_code="VALIDATION_ERROR",
            details=exc.details
        )
    
    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """Handle not found errors"""
        return await create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=str(exc) or "Resource not found",
            error_code="NOT_FOUND"
        )
    
    @app.exception_handler(UnauthorizedError)
    async def unauthorized_error_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
        """Handle unauthorized errors"""
        return await create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=str(exc) or "Not authenticated",
            error_code="UNAUTHORIZED"
        )
    
    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        """Handle forbidden errors"""
        return await create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            message=str(exc) or "Permission denied",
            error_code="FORBIDDEN"
        )
    
    @app.exception_handler(ConflictError)
    async def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
        """Handle conflict errors"""
        return await create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            message=str(exc) or "Resource conflict",
            error_code="CONFLICT"
        )
    
    @app.exception_handler(RequestValidationError)
    @app.exception_handler(PydanticValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError | PydanticValidationError
    ) -> JSONResponse:
        """Handle request validation errors"""
        if isinstance(exc, RequestValidationError):
            errors = [{"loc": ".".join(str(loc) for loc in e["loc"]), "msg": e["msg"]} 
                     for e in exc.errors()]
        else:
            errors = [{"loc": ".".join(str(loc) for loc in e["loc"]), "msg": e["msg"]} 
                     for e in exc.errors()]
            
        return await create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            details={"errors": errors}
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions"""
        logger = app.state.logger if hasattr(app.state, 'logger') else None
        if logger:
            logger.error(
                "Unhandled exception",
                exc_info=exc,
                extra={"path": request.url.path, "method": request.method}
            )
            
        return await create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR"
        )
