"""
WebSocket handler for generation updates - migrated to router.py

This module is kept for backwards compatibility. All functionality has been moved
to app.websocket.router for better organization and code clarity.
"""
import logging
from typing import Dict, Any

from fastapi import WebSocket
from app.websocket.router import websocket_endpoint as router_websocket_endpoint

logger = logging.getLogger(__name__)

# Re-export the websocket_endpoint from router for backwards compatibility
websocket_endpoint = router_websocket_endpoint

# This method is no longer used directly - functionality moved to router.py
async def handle_websocket_message(client_id: str, message: Dict[str, Any], connection_manager, chat_handler):
    """
    Deprecated: This method has been moved to app.websocket.router

    All WebSocket message handling now happens in the router module for improved
    code organization and debugging capabilities.
    """
    logger.warning(f"Deprecated handler called for message type: {message.get('type')}")
    from app.websocket.router import handle_websocket_message as router_handle_message
    await router_handle_message(client_id, message, connection_manager, chat_handler)

