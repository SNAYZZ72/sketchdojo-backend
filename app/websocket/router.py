"""
WebSocket router for message handling
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

from app.dependencies import get_chat_handler_for_websocket
from app.websocket.connection_manager import get_connection_manager
from app.websocket.handlers.tool_handler import get_tool_handler

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint handling all message types
    
    Args:
        websocket: The WebSocket connection object
    """
    # Use client_id from query parameters if provided, otherwise generate new
    client_id = websocket.query_params.get("client_id", str(uuid4()))
    logger.debug(f"Using client_id: {client_id} (from query params: {websocket.query_params.get('client_id') is not None})")
    connection_manager = get_connection_manager()
    # Get the chat handler directly
    chat_handler = await get_chat_handler_for_websocket()
    tool_handler = get_tool_handler()
    
    # Grant permissions based on tool categories
    from app.config import get_settings
    settings = get_settings()
    
    # Get all available tools
    available_tools = [tool.tool_id for tool in tool_handler.tool_registry.tools.values()]
    
    # Define tool categories
    tool_categories = {
        "basic": ["echo", "weather"],
        "webtoon": [
            tool_id for tool_id in available_tools 
            if any(tool_id.startswith(prefix) for prefix in ["create_", "edit_", "remove_", "add_"])
        ],
        # Add more categories as needed
    }
    
    # Determine which categories to grant based on settings or client type
    # Default to granting basic and webtoon tools
    categories_to_grant = settings.default_tool_categories if hasattr(settings, "default_tool_categories") else ["basic", "webtoon"]
    
    # Build the list of tools to grant
    granted_tools = []
    for category in categories_to_grant:
        if category in tool_categories:
            granted_tools.extend(tool_categories[category])
    
    # Grant the permissions
    tool_handler.grant_permissions(client_id, granted_tools)
    
    logger.info(f"Granted tool permissions for client {client_id}: {', '.join(granted_tools)}")

    try:
        logger.info(f"New WebSocket connection from client {client_id}")
        await connection_manager.connect(websocket, client_id)

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.debug(f"Received raw WebSocket message: {data[:200]}...")

            try:
                message = json.loads(data)
                logger.debug(f"Parsed message type: {message.get('type', 'unknown')}")
                # Use handle_websocket_message to process the message
                await handle_websocket_message(
                    client_id, message, connection_manager, chat_handler
                )
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}: {data[:100]}...")
                await connection_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"},
                    client_id,
                )
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {str(e)}")
                logger.exception("Full exception details:")
                await connection_manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Error processing message: {str(e)}",
                    },
                    client_id,
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnect for client {client_id}")
        await chat_handler.handle_client_disconnect(client_id)
        await connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        logger.exception("Full exception details:")
        await chat_handler.handle_client_disconnect(client_id)
        await connection_manager.disconnect(client_id)


class MessageHandlerRegistry:
    """Registry for WebSocket message handlers"""
    
    def __init__(self, connection_manager, chat_handler):
        """Initialize the message handler registry
        
        Args:
            connection_manager: The WebSocket connection manager
            chat_handler: The chat handler instance
        """
        self.handlers = {}
        self.connection_manager = connection_manager
        self.chat_handler = chat_handler
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register all message handlers"""
        # Task subscription handlers
        self.register("subscribe_task", self._handle_subscribe_task)
        self.register("unsubscribe_task", self._handle_unsubscribe_task)
        
        # Chat message handlers
        self.register("join_chat_room", self._handle_join_room)
        self.register("join_room", self._handle_join_room)  # alias
        self.register("leave_chat_room", self._handle_leave_room)
        self.register("chat_message", self._handle_chat_message)
        self.register("typing_indicator", self._handle_typing_indicator)
        self.register("tool_discovery", self._handle_tool_discovery)
        
        # Utility message handlers
        self.register("ping", self._handle_ping)
        self.register("get_stats", self._handle_stats)
        self.register("get_room_info", self._handle_room_info)
    
    def register(self, message_type: str, handler_func) -> None:
        """Register a message handler function
        
        Args:
            message_type: The message type to handle
            handler_func: The async function that handles this message type
        """
        self.handlers[message_type] = handler_func
    
    async def handle_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle an incoming WebSocket message
        
        Args:
            client_id: The client ID
            message: The message to handle
        """
        message_type = message.get("type")
        logger.info(f"Processing message type '{message_type}' from client {client_id}")
        
        handler = self.handlers.get(message_type)
        if handler:
            await handler(client_id, message)
        else:
            logger.warning(f"Unknown message type from client {client_id}: {message_type}")
            await self.connection_manager.send_personal_message(
                {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                },
                client_id,
            )
    
    # Task subscription handlers
    async def _handle_subscribe_task(self, client_id: str, message: Dict[str, Any]) -> None:
        task_id = message.get("task_id")
        if task_id:
            logger.debug(f"Client {client_id} subscribing to task {task_id}")
            await self.connection_manager.subscribe_to_task(client_id, task_id)
        else:
            await self.connection_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "task_id is required for subscription",
                },
                client_id,
            )
    
    async def _handle_unsubscribe_task(self, client_id: str, message: Dict[str, Any]) -> None:
        task_id = message.get("task_id")
        if task_id:
            logger.debug(f"Client {client_id} unsubscribing from task {task_id}")
            await self.connection_manager.unsubscribe_from_task(client_id, task_id)
        else:
            await self.connection_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "task_id is required for unsubscription",
                },
                client_id,
            )
    
    # Chat message handlers
    async def _handle_join_room(self, client_id: str, message: Dict[str, Any]) -> None:
        logger.info(f"Client {client_id} joining chat room: {message.get('room_id')}")
        await self.chat_handler.handle_join_room(client_id, message)
    
    async def _handle_leave_room(self, client_id: str, message: Dict[str, Any]) -> None:
        logger.info(f"Client {client_id} leaving chat room")
        await self.chat_handler.handle_leave_room(client_id, message)
    
    async def _handle_chat_message(self, client_id: str, message: Dict[str, Any]) -> None:
        logger.info(f"Routing chat message from client {client_id} to chat_handler")
        await self.chat_handler.handle_chat_message(client_id, message)
    
    async def _handle_typing_indicator(self, client_id: str, message: Dict[str, Any]) -> None:
        await self.chat_handler.handle_typing_indicator(client_id, message)
    
    async def _handle_tool_discovery(self, client_id: str, message: Dict[str, Any]) -> None:
        await self.chat_handler.handle_tool_discovery(client_id, message)
    
    # Utility message handlers
    async def _handle_ping(self, client_id: str, message: Dict[str, Any]) -> None:
        await self.connection_manager.send_personal_message(
            {"type": "pong", "timestamp": str(datetime.now(UTC))}, client_id
        )
    
    async def _handle_stats(self, client_id: str, message: Dict[str, Any]) -> None:
        stats = self.connection_manager.get_connection_stats()
        await self.connection_manager.send_personal_message(
            {"type": "stats", "data": stats}, client_id
        )
    
    async def _handle_room_info(self, client_id: str, message: Dict[str, Any]) -> None:
        room_id = message.get("room_id")
        if room_id:
            room_info = self.chat_handler.get_room_info(room_id)
            await self.connection_manager.send_personal_message(
                {"type": "room_info", "data": room_info}, client_id
            )
        else:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "room_id is required"}, client_id
            )


async def handle_websocket_message(
    client_id: str, message: Dict[str, Any], connection_manager, chat_handler
) -> None:
    """Handle incoming WebSocket messages using the handler registry
    
    Args:
        client_id: Unique identifier for the client
        message: The decoded message from the client
        connection_manager: WebSocket connection manager instance
        chat_handler: ChatHandler instance for chat-related operations
    """
    # Create handler registry on first use
    if not hasattr(handle_websocket_message, "_handler_registry"):
        handle_websocket_message._handler_registry = MessageHandlerRegistry(connection_manager, chat_handler)
    
    # Handle the message
    await handle_websocket_message._handler_registry.handle_message(client_id, message)
