"""
WebSocket middleware for cross-cutting concerns.

This module provides middleware components that can process WebSocket messages
before they reach the main handlers, enabling cross-cutting concerns like
authentication, logging, and metrics collection.
"""

from typing import Any, Dict, Optional, Protocol, TypeVar, runtime_checkable

from fastapi import WebSocket

# Type variable for the next middleware/handler in the chain
T = TypeVar('T')

@runtime_checkable
class WebSocketMiddleware(Protocol):
    """Protocol for WebSocket middleware components.
    
    Middleware components can process incoming messages before they reach the
    main handlers, and outgoing messages before they are sent to clients.
    """
    
    async def __call__(
        self,
        websocket: WebSocket,
        client_id: str,
        message: Dict[str, Any],
        call_next: T,
    ) -> Any:
        """Process an incoming WebSocket message.
        
        Args:
            websocket: The WebSocket connection.
            client_id: The ID of the client that sent the message.
            message: The message data as a dictionary.
            call_next: The next middleware or handler in the chain.
            
        Returns:
            The result of calling the next middleware or handler.
        """
        ...
