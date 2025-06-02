"""
WebSocket handler for real-time chat functionality
"""
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List
from uuid import uuid4

from app.websocket.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)


class ChatHandler:
    """Handle real-time chat functionality for webtoon collaboration"""

    def __init__(self):
        self.connection_manager = get_connection_manager()
        self.chat_rooms: Dict[str, List[str]] = {}  # room_id -> list of client_ids
        self.client_rooms: Dict[str, str] = {}  # client_id -> room_id

    async def handle_join_room(self, client_id: str, message: Dict[str, Any]):
        """Handle client joining a chat room"""
        room_id = message.get("room_id")
        if not room_id:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "room_id is required"}, client_id
            )
            return

        # Remove client from previous room if any
        await self._leave_current_room(client_id)

        # Add client to new room
        if room_id not in self.chat_rooms:
            self.chat_rooms[room_id] = []

        self.chat_rooms[room_id].append(client_id)
        self.client_rooms[client_id] = room_id

        # Notify client of successful join
        await self.connection_manager.send_personal_message(
            {
                "type": "chat_room_joined",
                "room_id": room_id,
                "participants": len(self.chat_rooms[room_id]),
            },
            client_id,
        )

        # Notify other participants
        await self._broadcast_to_room(
            room_id,
            {
                "type": "participant_joined",
                "room_id": room_id,
                "participants": len(self.chat_rooms[room_id]),
            },
            exclude_client=client_id,
        )

        logger.info(f"Client {client_id} joined chat room {room_id}")

    async def handle_leave_room(self, client_id: str, message: Dict[str, Any]):
        """Handle client leaving a chat room"""
        await self._leave_current_room(client_id)

    async def handle_chat_message(self, client_id: str, message: Dict[str, Any]):
        """Handle chat message from client"""
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "You must join a room first"},
                client_id,
            )
            return

        chat_text = message.get("text", "").strip()
        if not chat_text:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "Message text cannot be empty"},
                client_id,
            )
            return

        # Create chat message
        chat_message = {
            "type": "chat_message",
            "room_id": room_id,
            "client_id": client_id,
            "text": chat_text,
            "timestamp": datetime.now(UTC).isoformat(),
            "message_id": str(uuid4()),
        }

        # Broadcast to all room participants
        await self._broadcast_to_room(room_id, chat_message)

        logger.debug(
            f"Chat message from {client_id} in room {room_id}: {chat_text[:50]}"
        )

    async def handle_typing_indicator(self, client_id: str, message: Dict[str, Any]):
        """Handle typing indicator"""
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            return

        is_typing = message.get("is_typing", False)

        typing_message = {
            "type": "typing_indicator",
            "room_id": room_id,
            "client_id": client_id,
            "is_typing": is_typing,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Broadcast to other room participants
        await self._broadcast_to_room(room_id, typing_message, exclude_client=client_id)

    async def handle_client_disconnect(self, client_id: str):
        """Handle client disconnection"""
        await self._leave_current_room(client_id)

    async def _leave_current_room(self, client_id: str):
        """Remove client from their current room"""
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            return

        # Remove from room
        if room_id in self.chat_rooms and client_id in self.chat_rooms[room_id]:
            self.chat_rooms[room_id].remove(client_id)

            # Clean up empty rooms
            if not self.chat_rooms[room_id]:
                del self.chat_rooms[room_id]
            else:
                # Notify remaining participants
                await self._broadcast_to_room(
                    room_id,
                    {
                        "type": "participant_left",
                        "room_id": room_id,
                        "participants": len(self.chat_rooms[room_id]),
                    },
                )

        # Remove client room mapping
        if client_id in self.client_rooms:
            del self.client_rooms[client_id]

        logger.info(f"Client {client_id} left chat room {room_id}")

    async def _broadcast_to_room(
        self, room_id: str, message: Dict[str, Any], exclude_client: str = None
    ):
        """Broadcast message to all clients in a room"""
        if room_id not in self.chat_rooms:
            return

        for client_id in self.chat_rooms[room_id]:
            if exclude_client and client_id == exclude_client:
                continue

            await self.connection_manager.send_personal_message(message, client_id)

    def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """Get information about a chat room"""
        if room_id not in self.chat_rooms:
            return {"exists": False}

        return {
            "exists": True,
            "room_id": room_id,
            "participant_count": len(self.chat_rooms[room_id]),
            "participants": self.chat_rooms[room_id],
        }

    def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """Get information about a client"""
        room_id = self.client_rooms.get(client_id)
        return {
            "client_id": client_id,
            "current_room": room_id,
            "in_room": room_id is not None,
        }


# Global chat handler instance
_chat_handler = None


def get_chat_handler() -> ChatHandler:
    """Get the global chat handler instance"""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler()
    return _chat_handler
