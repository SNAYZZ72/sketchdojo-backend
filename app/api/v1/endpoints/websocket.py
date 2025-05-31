# =============================================================================
# app/api/v1/endpoints/websocket.py
# =============================================================================
import json
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_websocket_user
from app.core.websocket import manager
from app.schemas.user import UserResponse

router = APIRouter()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint for real-time updates."""
    connection_id = str(uuid.uuid4())

    try:
        # Authenticate user from token
        user = await get_websocket_user(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect to manager
        await manager.connect(websocket, connection_id, user.id)

        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "connection_id": connection_id,
            "message": "WebSocket connection established",
        }
        await manager.send_personal_message(welcome_message, connection_id)

        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                await handle_websocket_message(message, connection_id, user.id, db)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_message = {"type": "error", "message": "Invalid JSON format"}
                await manager.send_personal_message(error_message, connection_id)
            except Exception as e:
                error_message = {"type": "error", "message": str(e)}
                await manager.send_personal_message(error_message, connection_id)

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        manager.disconnect(connection_id)


async def handle_websocket_message(
    message: Dict[str, Any], connection_id: str, user_id: uuid.UUID, db: AsyncSession
):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")

    if message_type == "ping":
        # Respond to ping
        pong_message = {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        await manager.send_personal_message(pong_message, connection_id)

    elif message_type == "subscribe_task":
        # Subscribe to task updates
        task_id = message.get("task_id")
        if task_id:
            # Verify user owns the task
            # This would check database ownership
            response = {
                "type": "subscription_confirmed",
                "resource_type": "task",
                "resource_id": task_id,
            }
            await manager.send_personal_message(response, connection_id)

    elif message_type == "subscribe_webtoon":
        # Subscribe to webtoon updates
        webtoon_id = message.get("webtoon_id")
        if webtoon_id:
            # Verify user owns the webtoon
            response = {
                "type": "subscription_confirmed",
                "resource_type": "webtoon",
                "resource_id": webtoon_id,
            }
            await manager.send_personal_message(response, connection_id)

    elif message_type == "get_status":
        # Get current connection status
        status_message = {
            "type": "status",
            "connection_id": connection_id,
            "user_id": str(user_id),
            "connections": manager.get_user_connection_count(user_id),
        }
        await manager.send_personal_message(status_message, connection_id)

    else:
        # Unknown message type
        error_message = {"type": "error", "message": f"Unknown message type: {message_type}"}
        await manager.send_personal_message(error_message, connection_id)
