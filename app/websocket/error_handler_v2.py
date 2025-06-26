"""
WebSocket error handler implementation using the new BaseErrorHandler.

This module provides a WebSocket-specific error handler that extends the
BaseErrorHandler to provide WebSocket-specific error handling functionality.
"""
from typing import Any, Dict, Optional, Type, TypeVar, Callable, Awaitable, cast
from fastapi import WebSocket

from app.core.error_handling.base_error_handler import BaseErrorHandler
from app.websocket.connection_manager import ConnectionManager
from app.websocket.exceptions import WebSocketError, send_error

T = TypeVar('T')

class WebSocketErrorHandler(BaseErrorHandler[WebSocketError]):
    """
    WebSocket error handler that extends BaseErrorHandler with WebSocket-specific
    functionality.
    """
    
    def __init__(
        self,
        connection_manager: Optional[ConnectionManager] = None,
        include_error_details: bool = False
    ):
        """Initialize the WebSocket error handler.
        
        Args:
            connection_manager: Optional connection manager for sending error messages
            include_error_details: Whether to include full error details by default
        """
        super().__init__(
            default_error_type=WebSocketError,
            logger_name=__name__,
            include_error_details=include_error_details
        )
        self.connection_manager = connection_manager or ConnectionManager()
    
    async def send_error(
        self,
        error_response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send an error response via WebSocket.
        
        Args:
            error_response: The formatted error response
            context: Optional context containing WebSocket connection info
        """
        if not context:
            context = {}
            
        websocket = context.get('websocket')
        client_id = context.get('client_id')
        
        # Create the error object
        error = WebSocketError(
            message=error_response.get('message', 'An error occurred'),
            code=error_response.get('code', 'error'),
            status_code=error_response.get('status_code', 400),
            details=error_response.get('details', {})
        )
        
        # If we have a client_id, use the connection manager (prioritize this over direct websocket)
        if client_id is not None:
            await self._send_error_to_client(client_id, error_response)
        # Otherwise, if we have a websocket, use that for sending the error
        elif websocket is not None:
            # Use the imported send_error function
            await send_error(
                websocket,
                error,
                include_details=self.include_error_details
            )
        # If neither is available, log a warning
        else:
            self.logger.warning(
                "Cannot send WebSocket error - no websocket or client_id in context",
                extra={"error_response": error_response, "context": context}
            )
    
    async def _send_error_to_client(
        self,
        client_id: str,
        error_response: Dict[str, Any]
    ) -> None:
        """Send an error message to a specific client via the connection manager."""
        from app.websocket.exceptions import format_error
        
        error = WebSocketError(
            message=error_response.get('message', 'An error occurred'),
            code=error_response.get('code', 'error'),
            status_code=error_response.get('status_code', 400),
            details=error_response.get('details', {})
        )
        
        error_message = format_error(error, include_details=self.include_error_details)
        await self.connection_manager.send_personal_message(error_message, client_id)
    
    def _get_context_from_args(
        self,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract WebSocket context from handler arguments."""
        context: Dict[str, Any] = {}
        
        # Look for WebSocket in both args and kwargs
        for arg in args:
            if isinstance(arg, WebSocket):
                context['websocket'] = arg
                break
        
        # Check kwargs for common WebSocket handler parameters
        if 'websocket' in kwargs:
            context['websocket'] = kwargs['websocket']
        if 'client_id' in kwargs:
            context['client_id'] = kwargs['client_id']
        if 'message' in kwargs:
            context['message'] = kwargs['message']
            
        return context


# Global error handler instance
error_handler = WebSocketErrorHandler()


def get_error_handler() -> WebSocketErrorHandler:
    """Get the global WebSocket error handler."""
    return error_handler
