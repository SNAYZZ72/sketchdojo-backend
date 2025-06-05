"""
WebSocket handler for generation updates with chat integration
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

from app.websocket.connection_manager import get_connection_manager
from app.websocket.handlers.chat_handler import get_chat_handler
from app.websocket.handlers.tool_handler import get_tool_handler

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint with chat support"""
    # Generate client ID
    client_id = str(uuid4())
    connection_manager = get_connection_manager()
    chat_handler = get_chat_handler()
    tool_handler = get_tool_handler()
    
    # Grant default tool permissions to new clients
    tool_handler.grant_permissions(client_id, ["echo", "weather"])

    try:
        await connection_manager.connect(websocket, client_id)

        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_websocket_message(
                    client_id, message, connection_manager, chat_handler
                )
            except json.JSONDecodeError:
                await connection_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"},
                    client_id,
                )
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {str(e)}")
                await connection_manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Error processing message: {str(e)}",
                    },
                    client_id,
                )

    except WebSocketDisconnect:
        await chat_handler.handle_client_disconnect(client_id)
        await connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        await chat_handler.handle_client_disconnect(client_id)
        await connection_manager.disconnect(client_id)


async def handle_websocket_message(
    client_id: str, message: Dict[str, Any], connection_manager, chat_handler
):
    """Handle incoming WebSocket messages with chat support"""
    message_type = message.get("type")

    # Task subscription messages
    if message_type == "subscribe_task":
        task_id = message.get("task_id")
        if task_id:
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
    elif message_type == "join_chat_room":
        await chat_handler.handle_join_room(client_id, message)

    elif message_type == "leave_chat_room":
        await chat_handler.handle_leave_room(client_id, message)

    elif message_type == "chat_message":
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
        await connection_manager.send_personal_message(
            {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
            },
            client_id,
        )
