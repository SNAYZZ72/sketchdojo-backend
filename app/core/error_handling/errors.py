"""
Custom exceptions for the application.
"""
from typing import Any, Dict, List, Optional, Union


class AppError(Exception):
    """Base class for all application-specific exceptions."""
    
    def __init__(
        self, 
        message: str = "An error occurred",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        """Initialize the error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class BadRequestError(AppError):
    """Raised when the request is malformed or contains invalid data."""
    
    def __init__(self, message: str = "Invalid request", details: Optional[Dict[str, Any]] = None):
        """Initialize the bad request error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="BAD_REQUEST",
            details=details or {},
            status_code=400,
        )


class InternalServerError(AppError):
    """Raised when an unexpected error occurs on the server."""
    
    def __init__(self, message: str = "Internal server error", details: Optional[Dict[str, Any]] = None):
        """Initialize the internal server error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            details=details or {},
            status_code=500,
        )


class ValidationError(AppError):
    """Raised when input validation fails."""
    
    def __init__(
        self, 
        message: str = "Validation failed",
        errors: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        field: Optional[str] = None,
    ):
        """Initialize the validation error.
        
        Args:
            message: Human-readable error message
            errors: List of validation errors or a single error dictionary
            field: Field that failed validation (if applicable)
        """
        details = {"errors": errors} if errors else {}
        if field:
            details["field"] = field
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400,
        )


class NotFoundError(AppError):
    """Raised when a resource is not found."""
    
    def __init__(
        self, 
        resource: str = "Resource",
        resource_id: Optional[Any] = None,
        message: Optional[str] = None,
    ):
        """Initialize the not found error.
        
        Args:
            resource: Type of resource that was not found
            resource_id: ID of the resource that was not found
            message: Custom error message (will be generated if not provided)
        """
        if message is None:
            if resource_id is not None:
                message = f"{resource} with ID '{resource_id}' not found"
            else:
                message = f"{resource} not found"
                
        details = {"resource": resource}
        if resource_id is not None:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details,
            status_code=404,
        )


class UnauthorizedError(AppError):
    """Raised when authentication is required but not provided or invalid."""
    
    def __init__(self, message: str = "Authentication required"):
        """Initialize the unauthorized error."""
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenError(AppError):
    """Raised when the user doesn't have permission to access a resource."""
    
    def __init__(self, message: str = "Permission denied"):
        """Initialize the forbidden error."""
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
        )


class ConflictError(AppError):
    """Raised when a resource conflict occurs (e.g., duplicate entry)."""
    
    def __init__(self, message: str = "Resource already exists"):
        """Initialize the conflict error."""
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
        )


class RateLimitError(AppError):
    """Raised when rate limiting is applied."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        """Initialize the rate limit error.
        
        Args:
            message: Error message
            retry_after: Number of seconds to wait before retrying
        """
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=429,
        )


class ServiceUnavailableError(AppError):
    """Raised when a required service is unavailable."""
    
    def __init__(
        self, 
        service: str = "Service",
        message: Optional[str] = None,
    ):
        """Initialize the service unavailable error.
        
        Args:
            service: Name of the unavailable service
            message: Custom error message (will be generated if not provided)
        """
        if message is None:
            message = f"{service} is currently unavailable"
            
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
            status_code=503,
        )


class BadGatewayError(AppError):
    """Raised when an invalid response is received from an upstream server."""
    
    def __init__(self, message: str = "Bad gateway"):
        """Initialize the bad gateway error."""
        super().__init__(
            message=message,
            error_code="BAD_GATEWAY",
            status_code=502,
        )


class GatewayTimeoutError(AppError):
    """Raised when a request to an upstream server times out."""
    
    def __init__(self, message: str = "Gateway timeout"):
        """Initialize the gateway timeout error."""
        super().__init__(
            message=message,
            error_code="GATEWAY_TIMEOUT",
            status_code=504,
        )
