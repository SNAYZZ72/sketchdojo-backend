"""
Base WebSocket handler class

This module provides a base class for all WebSocket handlers in the application.
It encapsulates common functionality like dependency injection, error handling,
and message routing.
"""
import abc
import inspect
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar, Union

from fastapi import WebSocket
from pydantic import BaseModel

from app.websocket.connection_manager import ConnectionManager, get_connection_manager
from app.websocket.error_handler import get_error_handler
from app.websocket.events import WebSocketEvent
from app.websocket.exceptions import WebSocketError, WebSocketValidationError

logger = logging.getLogger(__name__)

# Type variable for message data
MessageData = Union[Dict[str, Any], BaseModel, str, bytes]

# Type variable for handler return type
T = TypeVar('T')

# Type alias for handler methods
HandlerMethod = Callable[..., Awaitable[None]]


class BaseWebSocketHandler(abc.ABC):
    """
    Base class for WebSocket message handlers.
    
    This class provides common functionality for handling WebSocket messages,
    including dependency injection, error handling, and message routing.
    """
    
    def __init__(
        self,
        connection_manager: Optional[ConnectionManager] = None,
        **dependencies: Any
    ):
        """
        Initialize the WebSocket handler.
        
        Args:
            connection_manager: The WebSocket connection manager
            **dependencies: Additional dependencies to be injected into handler methods
        """
        self.connection_manager = connection_manager or get_connection_manager()
        self.dependencies = dependencies
        self._message_handlers: Dict[str, HandlerMethod] = {}
        self._register_message_handlers()
    
    def _register_message_handlers(self) -> None:
        """
        Register all message handler methods.
        
        This method scans the class for methods decorated with @message_handler
        and registers them in the _message_handlers dictionary.
        """
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, '_message_type'):
                self._message_handlers[method._message_type] = method
    
    async def handle_message(
        self,
        client_id: str,
        message: Dict[str, Any],
        websocket: Optional[WebSocket] = None
    ) -> None:
        """
        Handle an incoming WebSocket message.
        
        Args:
            client_id: The ID of the client that sent the message
            message: The message data as a dictionary
            websocket: Optional WebSocket connection object
        """
        message_type = message.get('type')
        if not message_type:
            error = WebSocketValidationError("Message type is required")
            await self.handle_error(client_id, message, error, websocket)
            return
        
        handler = self._message_handlers.get(message_type)
        if not handler:
            error = WebSocketValidationError(f"No handler for message type: {message_type}")
            await self.handle_error(client_id, message, error, websocket)
            return
            
        try:
            # Prepare handler arguments
            kwargs = {
                'client_id': client_id,
                'message': message,
                'websocket': websocket,
                **self.dependencies
            }
            
            # Filter kwargs to only include parameters that the handler accepts
            sig = inspect.signature(handler)
            valid_kwargs = {
                k: v for k, v in kwargs.items()
                if k in sig.parameters
            }
            
            # Call the handler
            await handler(**valid_kwargs)
            
        except Exception as e:
            # The error will be handled by the error handler
            await self.handle_error(client_id, message, e, websocket)
    
    async def handle_error(
        self,
        client_id: str,
        message: Dict[str, Any],
        error: Exception,
        websocket: Optional[WebSocket] = None,
        **kwargs
    ) -> None:
        """
        Handle errors that occur during message processing.
        
        This method is kept for backward compatibility but delegates to the
        centralized error handler.
        
        Args:
            client_id: The ID of the client that sent the message
            message: The message that caused the error
            error: The exception that was raised
            websocket: Optional WebSocket connection object
            **kwargs: Additional keyword arguments (for compatibility with super() calls)
        """
        error_handler = get_error_handler()
        await error_handler.handle_error(
            error=error,
            websocket=websocket,
            client_id=client_id,
            message=message,
            include_details=False
        )
        
        # Log a deprecation warning
        import warnings
        warnings.warn(
            "BaseWebSocketHandler.handle_error() is deprecated. "
            "Use the centralized error handler from app.websocket.error_handler instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    async def send_message(
        self,
        client_id: str,
        message: MessageData,
        message_type: Optional[str] = None
    ) -> None:
        """
        Send a message to a specific client.
        
        Args:
            client_id: The ID of the client to send the message to
            message: The message data to send
            message_type: Optional message type (if not provided, will be determined from message)
        """
        if isinstance(message, WebSocketEvent):
            message_dict = message.to_dict()
        elif isinstance(message, BaseModel):
            message_dict = message.dict()
        elif isinstance(message, dict):
            message_dict = message.copy()
            if message_type:
                message_dict['type'] = message_type
        else:
            message_dict = {'type': message_type or 'message', 'data': message}
        
        await self.connection_manager.send_personal_message(message_dict, client_id)
    
    async def broadcast(
        self,
        message: MessageData,
        room_id: Optional[str] = None,
        exclude_clients: Optional[set[str]] = None,
        message_type: Optional[str] = None
    ) -> None:
        """
        Broadcast a message to multiple clients.
        
        Args:
            message: The message data to broadcast
            room_id: Optional room ID to broadcast to (if None, broadcasts to all connected clients)
            exclude_clients: Set of client IDs to exclude from the broadcast
            message_type: Optional message type (if not provided, will be determined from message)
        """
        if isinstance(message, WebSocketEvent):
            message_dict = message.to_dict()
        elif isinstance(message, BaseModel):
            message_dict = message.dict()
        elif isinstance(message, dict):
            message_dict = message.copy()
            if message_type:
                message_dict['type'] = message_type
        else:
            message_dict = {'type': message_type or 'broadcast', 'data': message}
        
        if room_id:
            # Broadcast to a specific room
            await self.connection_manager.broadcast_to_room(
                room_id=room_id,
                message=message_dict,
                exclude_clients=exclude_clients or set()
            )
        else:
            # Broadcast to all connected clients - pass message as a positional argument
            await self.connection_manager.broadcast(
                message_dict,
                exclude_clients=exclude_clients or set()
            )


def message_handler(message_type: str) -> Callable[[HandlerMethod], HandlerMethod]:
    """
    Decorator to mark a method as a message handler for a specific message type.
    
    Args:
        message_type: The message type that this handler should process
        
    Returns:
        A decorator function that registers the method as a handler
    """
    def decorator(method: HandlerMethod) -> HandlerMethod:
        method._message_type = message_type
        return method
    return decorator
