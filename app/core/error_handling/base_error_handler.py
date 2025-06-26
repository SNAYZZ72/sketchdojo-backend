"""
Base error handler for consistent error handling across the application.

This module provides a base class for error handling that can be extended
for different contexts (WebSocket, HTTP, etc.) while maintaining consistent
error handling patterns.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Type, TypeVar, Callable, Awaitable, Generic, cast

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

class BaseErrorHandler(Generic[E]):
    """
    Base class for error handlers that provides common error handling functionality.
    
    This class is designed to be extended by context-specific error handlers
    (e.g., WebSocket, HTTP) to provide consistent error handling patterns.
    """
    
    def __init__(
        self,
        default_error_type: Type[E],
        logger_name: Optional[str] = None,
        include_error_details: bool = False
    ):
        """Initialize the error handler.
        
        Args:
            default_error_type: The default exception type to use when wrapping errors
            logger_name: Optional name for the logger (defaults to module name)
            include_error_details: Whether to include full error details by default
        """
        self.default_error_type = default_error_type
        self.include_error_details = include_error_details
        self.logger = logging.getLogger(logger_name or __name__)
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        include_details: Optional[bool] = None
    ) -> None:
        """Handle an error that occurred during processing.
        
        Args:
            error: The exception that was raised
            context: Optional context about where the error occurred
            include_details: Whether to include full error details
        """
        include_details = include_details if include_details is not None else self.include_error_details
        
        # Log the error
        self._log_error(error, context, include_details)
        
        # Format and send the error response
        error_response = self.format_error(error, include_details)
        await self.send_error(error_response, context)
    
    def _log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        include_details: bool = False
    ) -> None:
        """Log an error with context.
        
        Args:
            error: The exception to log
            context: Optional context about where the error occurred
            include_details: Whether to include full error details in the log
        """
        log_message = f"Error: {str(error)}"
        if context:
            log_message = f"{log_message} (context: {context})"
            
        if include_details or not isinstance(error, self.default_error_type):
            self.logger.exception(log_message)
        else:
            self.logger.error(log_message)
    
    def format_error(
        self,
        error: Exception,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """Format an exception as an error response.
        
        Args:
            error: The exception to format
            include_details: Whether to include full exception details
            
        Returns:
            A dictionary containing the error details
        """
        if isinstance(error, self.default_error_type):
            error_dict = {
                "code": getattr(error, "code", "error"),
                "message": str(error),
            }
            if include_details or hasattr(error, "details"):
                error_dict["details"] = getattr(error, "details", {})
            return error_dict
            
        # For unexpected errors, return a generic error message
        return {
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(error)} if include_details else {}
        }
    
    async def send_error(
        self,
        error_response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send an error response.
        
        This method must be implemented by subclasses to define how to send
        the error response (e.g., via WebSocket, HTTP response, etc.).
        
        Args:
            error_response: The formatted error response
            context: Optional context about where the error occurred
        """
        raise NotImplementedError("Subclasses must implement send_error")
    
    def wrap_async_handler(
        self,
        handler: Callable[..., Awaitable[T]],
        include_details: Optional[bool] = None
    ) -> Callable[..., Awaitable[Optional[T]]]:
        """Wrap an async handler function with error handling.
        
        Args:
            handler: The async handler function to wrap
            include_details: Whether to include full error details in the response
            
        Returns:
            A new async function that wraps the original handler with error handling
        """
        include_details = include_details if include_details is not None else self.include_error_details
        
        async def wrapped(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return await handler(*args, **kwargs)
            except Exception as e:
                context = self._get_context_from_args(args, kwargs)
                await self.handle_error(e, context, include_details)
                return None
        
        return wrapped
    
    def _get_context_from_args(
        self,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract context from handler arguments.
        
        This method can be overridden by subclasses to extract relevant context
        from the handler arguments.
        
        Args:
            args: Positional arguments passed to the handler
            kwargs: Keyword arguments passed to the handler
            
        Returns:
            A dictionary of context information
        """
        return {}
    
    def __call__(
        self,
        include_details: Optional[bool] = None
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[Optional[T]]]]:
        """Create a decorator for wrapping async handlers with error handling.
        
        Example:
            @error_handler()
            async def my_handler(arg1, arg2):
                # Handler implementation
                pass
        """
        def decorator(handler: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[Optional[T]]]:
            return self.wrap_async_handler(handler, include_details=include_details)
        return decorator
