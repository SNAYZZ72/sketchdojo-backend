"""
WebSocket router for message handling
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

from app.dependencies import get_chat_handler_for_websocket
from app.websocket.connection_manager import get_connection_manager
from app.websocket.handlers.tool_handler import get_tool_handler

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint handling all message types"""
    # Use client_id from query parameters if provided, otherwise generate new
    client_id = websocket.query_params.get("client_id", str(uuid4()))
    logger.debug(f"Using client_id: {client_id} (from query params: {websocket.query_params.get('client_id') is not None})")
    connection_manager = get_connection_manager()
    # Get the chat handler directly
    chat_handler = await get_chat_handler_for_websocket()
    tool_handler = get_tool_handler()
    
    # Grant permissions for all available tools to new clients
    available_tools = [tool.tool_id for tool in tool_handler.tool_registry.tools.values()]
    
    # Grant basic tools + all webtoon tools
    webtoon_tools = [tool_id for tool_id in available_tools if tool_id.startswith("create_") or 
                    tool_id.startswith("edit_") or tool_id.startswith("remove_") or 
                    tool_id.startswith("add_")]
    
    # Combine built-in tools with webtoon tools
    granted_tools = ["echo", "weather"] + webtoon_tools
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


async def handle_websocket_message(
    client_id: str, message: Dict[str, Any], connection_manager, chat_handler
):
    """Handle incoming WebSocket messages with chat support"""
    message_type = message.get("type")
    logger.info(f"Processing message type '{message_type}' from client {client_id}")

    # Task subscription messages
    if message_type == "subscribe_task":
        task_id = message.get("task_id")
        if task_id:
            logger.debug(f"Client {client_id} subscribing to task {task_id}")
            await connection_manager.subscribe_to_task(client_id, task_id)
        else:
            await connection_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "task_id is required for subscription",
                },
                client_id,
            )

    elif message_type == "unsubscribe_task":
        task_id = message.get("task_id")
        if task_id:
            logger.debug(f"Client {client_id} unsubscribing from task {task_id}")
            await connection_manager.unsubscribe_from_task(client_id, task_id)
        else:
            await connection_manager.send_personal_message(
                {
                    "type": "error",
                    "message": "task_id is required for unsubscription",
                },
                client_id,
            )

    # Chat messages
    elif message_type == "join_chat_room" or message_type == "join_room":
        logger.info(f"Client {client_id} joining chat room: {message.get('room_id')}")
        await chat_handler.handle_join_room(client_id, message)

    elif message_type == "leave_chat_room":
        logger.info(f"Client {client_id} leaving chat room")
        await chat_handler.handle_leave_room(client_id, message)

    elif message_type == "chat_message":
        logger.info(f"Routing chat message from client {client_id} to chat_handler")
        await chat_handler.handle_chat_message(client_id, message)

    elif message_type == "typing_indicator":
        await chat_handler.handle_typing_indicator(client_id, message)
        
    # Tool-related messages
    elif message_type == "tool_discovery":
        await chat_handler.handle_tool_discovery(client_id, message)

    # Utility messages
    elif message_type == "ping":
        await connection_manager.send_personal_message(
            {"type": "pong", "timestamp": str(datetime.now(UTC))}, client_id
        )

    elif message_type == "get_stats":
        stats = connection_manager.get_connection_stats()
        await connection_manager.send_personal_message(
            {"type": "stats", "data": stats}, client_id
        )

    elif message_type == "get_room_info":
        room_id = message.get("room_id")
        if room_id:
            room_info = chat_handler.get_room_info(room_id)
            await connection_manager.send_personal_message(
                {"type": "room_info", "data": room_info}, client_id
            )
        else:
            await connection_manager.send_personal_message(
                {"type": "error", "message": "room_id is required"}, client_id
            )

    else:
        logger.warning(f"Unknown message type from client {client_id}: {message_type}")
        await connection_manager.send_personal_message(
            {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
            },
            client_id,
        )
