"""
Logging middleware for WebSocket connections.

This module provides middleware for logging WebSocket messages and connection events.
"""
import json
import logging
from typing import Any, Dict, Optional

from fastapi import WebSocket

from . import WebSocketMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    """Middleware for logging WebSocket messages and connection events.
    
    This middleware logs:
    - Connection and disconnection events
    - Incoming and outgoing messages
    - Errors during message handling
    """
    
    async def __call__(
        self,
        websocket: WebSocket,
        client_id: str,
        message: Dict[str, Any],
        call_next: WebSocketMiddleware,
    ) -> Any:
        """Process a WebSocket message with logging.
        
        Args:
            websocket: The WebSocket connection.
            client_id: The ID of the client that sent the message.
            message: The message data as a dictionary.
            call_next: The next middleware or handler in the chain.
            
        Returns:
            The result of calling the next middleware or handler.
        """
        # Log incoming message
        message_type = message.get('type', 'unknown')
        logger.info(
            "Received message from client %s: %s", 
            client_id,
            json.dumps({"type": message_type, "client_id": client_id}, default=str)
        )
        
        try:
            # Call the next middleware/handler in the chain
            response = await call_next(websocket, client_id, message)
            
            # Log successful message processing
            if response and isinstance(response, dict):
                response_type = response.get('type', 'unknown')
                logger.info(
                    "Sending response to client %s: %s",
                    client_id,
                    json.dumps({"type": response_type, "client_id": client_id}, default=str)
                )
                
            return response
            
        except Exception as e:
            # Log any errors during message processing
            logger.exception(
                "Error processing message from client %s: %s",
                client_id,
                str(e)
            )
            raise
