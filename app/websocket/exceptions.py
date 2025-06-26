"""
WebSocket-specific exceptions and error handling.

This module defines custom exceptions for WebSocket-related errors and provides
a centralized way to handle and format these errors.
"""
from typing import Any, Dict, Optional
from fastapi import WebSocket


class WebSocketError(Exception):
    """Base class for all WebSocket-related errors."""
    def __init__(
        self, 
        message: str, 
        code: str = "websocket_error",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class WebSocketValidationError(WebSocketError):
    """Raised when a WebSocket message fails validation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=400,
            details=details
        )


class WebSocketAuthenticationError(WebSocketError):
    """Raised when authentication fails for a WebSocket connection."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="authentication_error",
            status_code=401
        )


class WebSocketAuthorizationError(WebSocketError):
    """Raised when a client is not authorized to perform an action."""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            message=message,
            code="authorization_error",
            status_code=403
        )


class WebSocketRateLimitError(WebSocketError):
    """Raised when a client exceeds rate limits."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            code="rate_limit_exceeded",
            status_code=429,
            details={"retry_after": retry_after}
        )


class WebSocketInternalError(WebSocketError):
    """Raised when an internal server error occurs."""
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            code="internal_error",
            status_code=500
        )


def format_error(
    error: Exception,
    include_details: bool = False
) -> Dict[str, Any]:
    """Format an exception as a WebSocket error message.
    
    Args:
        error: The exception to format
        include_details: Whether to include full exception details
        
    Returns:
        A dictionary containing the error details
    """
    if isinstance(error, WebSocketError):
        error_dict = {
            "type": "error",
            "code": error.code,
            "message": str(error),
        }
        if include_details or error.details:
            error_dict["details"] = error.details
    else:
        error_dict = {
            "type": "error",
            "code": "internal_error",
            "message": str(error) or "An unexpected error occurred",
        }
        if include_details:
            error_dict["details"] = {
                "exception_type": error.__class__.__name__,
            }
    
    return error_dict


async def send_error(
    websocket: WebSocket,
    error: Exception,
    include_details: bool = False
) -> None:
    """Send an error message through a WebSocket connection.
    
    Args:
        websocket: The WebSocket connection to send the error to
        error: The exception to send
        include_details: Whether to include full exception details
    """
    try:
        error_message = format_error(error, include_details=include_details)
        await websocket.send_json(error_message)
    except Exception as send_error:
        # If we can't send the error, log it and give up
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send error message: {send_error}")
        logger.error(f"Original error was: {error}", exc_info=True)
