# app/websocket/connection_manager.py
"""
WebSocket connection manager
"""
import json
import logging
from datetime import UTC, datetime
from typing import Dict, List, Set
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        # Active connections by client ID
        self.active_connections: Dict[str, WebSocket] = {}

        # Task subscriptions: task_id -> set of client_ids
        self.task_subscriptions: Dict[str, Set[str]] = {}

        # Client subscriptions: client_id -> set of task_ids
        self.client_subscriptions: Dict[str, Set[str]] = {}

        logger.info("Connection manager initialized")

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()

        logger.info(f"Client {client_id} connected")

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection_established",
                "client_id": client_id,
                "message": "Connected to SketchDojo WebSocket",
            },
            client_id,
        )

    async def disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Clean up subscriptions
        if client_id in self.client_subscriptions:
            task_ids = self.client_subscriptions[client_id].copy()
            for task_id in task_ids:
                await self.unsubscribe_from_task(client_id, task_id)
            del self.client_subscriptions[client_id]

        logger.info(f"Client {client_id} disconnected")

    async def disconnect_all(self):
        """Disconnect all clients"""
        for client_id in list(self.active_connections.keys()):
            await self.disconnect(client_id)

    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                await self.disconnect(client_id)

    async def subscribe_to_task(self, client_id: str, task_id: str):
        """Subscribe a client to task updates"""
        if client_id not in self.client_subscriptions:
            return False

        # Add to subscriptions
        self.client_subscriptions[client_id].add(task_id)

        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()
        self.task_subscriptions[task_id].add(client_id)

        logger.debug(f"Client {client_id} subscribed to task {task_id}")

        # Send confirmation
        await self.send_personal_message(
            {"type": "subscription_confirmed", "task_id": task_id}, client_id
        )

        return True

    async def unsubscribe_from_task(self, client_id: str, task_id: str):
        """Unsubscribe a client from task updates"""
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(task_id)

        if task_id in self.task_subscriptions:
            self.task_subscriptions[task_id].discard(client_id)

            # Clean up empty task subscriptions
            if not self.task_subscriptions[task_id]:
                del self.task_subscriptions[task_id]

        logger.debug(f"Client {client_id} unsubscribed from task {task_id}")

    async def broadcast_task_update(self, task_id: str, update: dict):
        """Broadcast task update to all subscribed clients"""
        if task_id not in self.task_subscriptions:
            return

        message = {"type": "task_update", "task_id": task_id, **update}

        # Send to all subscribed clients
        for client_id in self.task_subscriptions[task_id].copy():
            await self.send_personal_message(message, client_id)

    async def broadcast_generation_progress(
        self,
        task_id: str,
        progress_percentage: float,
        current_operation: str,
        additional_data: dict = None,
    ):
        """Broadcast generation progress update"""
        update = {
            "progress_percentage": progress_percentage,
            "current_operation": current_operation,
            "timestamp": str(datetime.now(UTC)),
        }

        if additional_data:
            update.update(additional_data)

        await self.broadcast_task_update(task_id, update)

    async def broadcast_generation_completed(
        self, task_id: str, webtoon_id: str, result_data: dict
    ):
        """Broadcast generation completion"""
        update = {
            "status": "completed",
            "webtoon_id": webtoon_id,
            "result_data": result_data,
            "timestamp": str(datetime.now(UTC)),
        }

        await self.broadcast_task_update(task_id, update)

    async def broadcast_generation_failed(self, task_id: str, error_message: str):
        """Broadcast generation failure"""
        update = {
            "status": "failed",
            "error_message": error_message,
            "timestamp": str(datetime.now(UTC)),
        }

        await self.broadcast_task_update(task_id, update)

    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "task_subscriptions": len(self.task_subscriptions),
            "total_subscriptions": sum(
                len(clients) for clients in self.task_subscriptions.values()
            ),
        }


# Global connection manager instance
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
