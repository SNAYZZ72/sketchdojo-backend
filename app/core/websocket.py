# =============================================================================
# app/core/websocket.py
# =============================================================================
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[UUID, Set[str]] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: UUID):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket

        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        # Store connection metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
        }

        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            # Remove from user connections
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")

            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Clean up
            del self.active_connections[connection_id]
            if connection_id in self.connection_metadata:
                del self.connection_metadata[connection_id]

            logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {str(e)}")
                self.disconnect(connection_id)

    async def send_user_message(self, message: Dict[str, Any], user_id: UUID):
        """Send a message to all connections for a specific user."""
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                await self.send_personal_message(message, connection_id)

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all active connections."""
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.send_personal_message(message, connection_id)

    async def send_task_update(self, task_id: UUID, user_id: UUID, update_data: Dict[str, Any]):
        """Send task progress update to user."""
        message = {
            "type": "task_update",
            "task_id": str(task_id),
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_user_message(message, user_id)

    async def send_panel_update(self, panel_id: UUID, user_id: UUID, update_data: Dict[str, Any]):
        """Send panel update to user."""
        message = {
            "type": "panel_update",
            "panel_id": str(panel_id),
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_user_message(message, user_id)

    async def send_webtoon_update(
        self, webtoon_id: UUID, user_id: UUID, update_data: Dict[str, Any]
    ):
        """Send webtoon update to user."""
        message = {
            "type": "webtoon_update",
            "webtoon_id": str(webtoon_id),
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.send_user_message(message, user_id)

    async def ping_connections(self):
        """Send ping to all connections to keep them alive."""
        ping_message = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
        await self.broadcast_message(ping_message)

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)

    def get_user_connection_count(self, user_id: UUID) -> int:
        """Get number of connections for a specific user."""
        return len(self.user_connections.get(user_id, set()))


# Global connection manager instance
manager = ConnectionManager()


async def start_ping_task():
    """Start background task to ping connections."""
    from app.core.config import settings

    while True:
        await asyncio.sleep(settings.websocket_ping_interval)
        await manager.ping_connections()
