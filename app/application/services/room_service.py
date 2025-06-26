"""
Room management service for WebSocket connections.

This service handles room creation, participant management, and room state.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from fastapi import WebSocket

from app.websocket.connection_manager import ConnectionManager
from app.websocket.exceptions import WebSocketError, WebSocketValidationError

logger = logging.getLogger(__name__)


class RoomService:
    """Service for managing WebSocket rooms and participants."""

    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        """Initialize the room service.
        
        Args:
            connection_manager: Optional connection manager for sending messages
        """
        self.connection_manager = connection_manager or ConnectionManager()
        self.rooms: Dict[str, Set[str]] = {}  # room_id -> set of client_ids
        self.client_rooms: Dict[str, str] = {}  # client_id -> room_id
        self.room_metadata: Dict[str, Dict] = {}  # room_id -> metadata

    async def create_room(
        self,
        room_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new room with optional metadata.
        
        Args:
            room_id: Optional custom room ID (UUID will be generated if not provided)
            metadata: Optional metadata for the room
            
        Returns:
            The created room ID
        """
        if not room_id:
            room_id = str(uuid4())
            
        if room_id in self.rooms:
            raise WebSocketError(f"Room {room_id} already exists", code="room_exists")
            
        self.rooms[room_id] = set()
        self.room_metadata[room_id] = metadata or {}
        logger.info(f"Created room {room_id}")
        return room_id

    async def join_room(
        self,
        client_id: str,
        room_id: str,
        websocket: Optional[WebSocket] = None
    ) -> None:
        """Add a client to a room.
        
        Args:
            client_id: The ID of the client joining
            room_id: The ID of the room to join
            websocket: Optional WebSocket connection for the client
            
        Raises:
            WebSocketError: If the room doesn't exist or client is already in a room
        """
        if room_id not in self.rooms:
            raise WebSocketError(f"Room {room_id} does not exist", code="room_not_found")
            
        if client_id in self.client_rooms:
            current_room = self.client_rooms[client_id]
            if current_room == room_id:
                return  # Already in this room
            raise WebSocketError(
                f"Client {client_id} is already in room {current_room}",
                code="already_in_room"
            )
            
        self.rooms[room_id].add(client_id)
        self.client_rooms[client_id] = room_id
        logger.info(f"Client {client_id} joined room {room_id}")
        
        # Notify other participants
        await self._notify_room_change(room_id, "participant_joined", {
            "client_id": client_id,
            "participants": len(self.rooms[room_id])
        }, exclude_client=client_id)

    async def leave_room(self, client_id: str) -> Optional[str]:
        """Remove a client from their current room.
        
        Args:
            client_id: The ID of the client leaving
            
        Returns:
            The ID of the room the client left, or None if not in any room
        """
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            return None
            
        if room_id in self.rooms:
            self.rooms[room_id].discard(client_id)
            
            # Notify other participants before potentially removing the room
            await self._notify_room_change(room_id, "participant_left", {
                "client_id": client_id,
                "participants": len(self.rooms[room_id])
            })
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]
                if room_id in self.room_metadata:
                    del self.room_metadata[room_id]
                logger.info(f"Room {room_id} is now empty and has been removed")
        
        # Remove client room mapping
        self.client_rooms.pop(client_id, None)
        logger.info(f"Client {client_id} left room {room_id}")
        return room_id

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_client: Optional[str] = None
    ) -> None:
        """Broadcast a message to all clients in a room.
        
        Args:
            room_id: The ID of the room to broadcast to
            message: The message to send
            exclude_client: Optional client ID to exclude from the broadcast
        """
        if room_id not in self.rooms:
            return
            
        for client_id in self.rooms[room_id]:
            if client_id == exclude_client:
                continue
                
            try:
                await self.connection_manager.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")

    async def get_room_info(self, room_id: str) -> dict:
        """Get information about a room.
        
        Args:
            room_id: The ID of the room
            
        Returns:
            Dictionary containing room information
        """
        if room_id not in self.rooms:
            return {"exists": False}
            
        return {
            "exists": True,
            "room_id": room_id,
            "participant_count": len(self.rooms[room_id]),
            "participants": list(self.rooms[room_id]),
            "metadata": self.room_metadata.get(room_id, {})
        }

    async def get_client_room(self, client_id: str) -> Optional[str]:
        """Get the room ID for a client.
        
        Args:
            client_id: The ID of the client
            
        Returns:
            The room ID if the client is in a room, None otherwise
        """
        return self.client_rooms.get(client_id)

    async def _notify_room_change(
        self,
        room_id: str,
        change_type: str,
        data: dict,
        exclude_client: Optional[str] = None
    ) -> None:
        """Notify room participants about a room change.
        
        Args:
            room_id: The ID of the room
            change_type: Type of change (e.g., 'participant_joined')
            data: Additional data to include in the notification
            exclude_client: Optional client ID to exclude from the notification
        """
        notification = {
            "type": "room_update",
            "room_id": room_id,
            "event": change_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast_to_room(room_id, notification, exclude_client=exclude_client)


# Global room service instance
_room_service = None


def get_room_service() -> RoomService:
    """Get the global room service instance."""
    global _room_service
    if _room_service is None:
        _room_service = RoomService()
    return _room_service
