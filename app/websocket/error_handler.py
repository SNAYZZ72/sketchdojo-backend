"""
WebSocket error handler.

This module provides a centralized way to handle and report WebSocket errors.
"""
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Callable, Awaitable

from fastapi import WebSocket

from app.websocket.exceptions import (
    WebSocketError,
    WebSocketInternalError,
    send_error
)
from app.websocket.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Type variable for handler return type
T = TypeVar('T')


class WebSocketErrorHandler:
    """Centralized error handler for WebSocket operations."""
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        """Initialize the error handler.
        
        Args:
            connection_manager: Optional connection manager for sending error messages
        """
        self.connection_manager = connection_manager or ConnectionManager()
    
    async def handle_error(
        self,
        error: Exception,
        websocket: Optional[WebSocket] = None,
        client_id: Optional[str] = None,
        message: Optional[Dict[str, Any]] = None,
        include_details: bool = False
    ) -> None:
        """Handle an error that occurred during WebSocket processing.
        
        Args:
            error: The exception that was raised
            websocket: Optional WebSocket connection to send the error to
            client_id: Optional client ID to send the error to
            message: Optional original message that caused the error
            include_details: Whether to include full error details in the response
        """
        # Log the error
        log_message = f"WebSocket error"
        if client_id:
            log_message += f" for client {client_id}"
        if message:
            log_message += f" (message: {message.get('type', 'unknown')})"
        
        if isinstance(error, WebSocketError):
            logger.warning(f"{log_message}: {str(error)}", exc_info=not include_details)
        else:
            logger.error(f"{log_message}: {str(error)}", exc_info=True)
        
        # Send error response if we have a way to send it
        if websocket is not None:
            await send_error(websocket, error, include_details=include_details)
        elif client_id is not None:
            await self._send_error_to_client(client_id, error, include_details)
    
    async def _send_error_to_client(
        self,
        client_id: str,
        error: Exception,
        include_details: bool = False
    ) -> None:
        """Send an error message to a specific client via the connection manager."""
        from app.websocket.exceptions import format_error
        
        error_message = format_error(error, include_details=include_details)
        await self.connection_manager.send_personal_message(error_message, client_id)
    
    def wrap_async_handler(
        self,
        handler: Callable[..., Awaitable[T]],
        include_details: bool = False
    ) -> Callable[..., Awaitable[Optional[T]]]:
        """Wrap an async handler function with error handling.
        
        Args:
            handler: The async handler function to wrap
            include_details: Whether to include full error details in the response
            
        Returns:
            A new async function that wraps the original handler with error handling
        """
        async def wrapped(*args, **kwargs) -> Optional[T]:
            websocket = kwargs.get('websocket')
            client_id = kwargs.get('client_id')
            message = kwargs.get('message')
            
            try:
                return await handler(*args, **kwargs)
            except Exception as e:
                await self.handle_error(
                    error=e,
                    websocket=websocket,
                    client_id=client_id,
                    message=message,
                    include_details=include_details
                )
                return None
        
        return wrapped
    
    def __call__(
        self,
        include_details: bool = False
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[Optional[T]]]]:
        """Create a decorator for wrapping async handlers with error handling.
        
        Example:
            @error_handler()
            async def my_handler(websocket: WebSocket, message: Dict[str, Any]) -> None:
                # Handler implementation
                pass
        """
        def decorator(handler: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[Optional[T]]]:
            return self.wrap_async_handler(handler, include_details=include_details)
        return decorator


# Global error handler instance
error_handler = WebSocketErrorHandler()


def get_error_handler() -> WebSocketErrorHandler:
    """Get the global WebSocket error handler."""
    return error_handler
