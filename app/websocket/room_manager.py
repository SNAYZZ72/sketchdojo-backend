"""
Room management for WebSocket connections.

This module provides a RoomManager class that handles the management of chat rooms
and client-room associations for WebSocket connections.
"""
import logging
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from fastapi import WebSocket

from app.websocket.connection_manager import ConnectionManager
from app.websocket.exceptions import WebSocketValidationError

logger = logging.getLogger(__name__)


class RoomManager:
    """
    Manages chat rooms and client-room associations.
    
    This class is responsible for:
    - Creating and removing rooms
    - Adding/removing clients from rooms
    - Tracking room participants
    - Broadcasting messages to rooms
    """
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        """
        Initialize the RoomManager.
        
        Args:
            connection_manager: The WebSocket connection manager
        """
        self.connection_manager = connection_manager or ConnectionManager()
        self.rooms: Dict[str, Set[str]] = {}  # room_id -> set of client_ids
        self.client_rooms: Dict[str, str] = {}  # client_id -> room_id
    
    async def create_room(self) -> str:
        """
        Create a new chat room.
        
        Returns:
            The ID of the newly created room
        """
        room_id = str(uuid4())
        self.rooms[room_id] = set()
        logger.info(f"Created new room: {room_id}")
        return room_id
    
    async def join_room(
        self, 
        client_id: str, 
        room_id: str,
        websocket: Optional[WebSocket] = None
    ) -> bool:
        """
        Add a client to a room, creating the room if it doesn't exist.
        
        Args:
            client_id: The ID of the client joining the room
            room_id: The ID of the room to join
            websocket: Optional WebSocket connection for sending notifications
            
        Returns:
            bool: True if the client was added to the room, False if already in the room
        """
        # Create room if it doesn't exist
        if room_id not in self.rooms:
            logger.info(f"Room {room_id} does not exist, creating it")
            self.rooms[room_id] = set()
        
        # Remove client from current room if already in one
        await self.leave_room(client_id, notify=False)
        
        # Add to new room
        self.rooms[room_id].add(client_id)
        self.client_rooms[client_id] = room_id
        
        logger.info(f"Client {client_id} joined room {room_id}")
        return True
    
    async def leave_room(
        self, 
        client_id: str, 
        notify: bool = True,
        websocket: Optional[WebSocket] = None
    ) -> Optional[str]:
        """
        Remove a client from their current room.
        
        Args:
            client_id: The ID of the client leaving
            notify: Whether to send leave notifications
            websocket: Optional WebSocket connection for sending notifications
            
        Returns:
            Optional[str]: The ID of the room the client left, or None if not in any room
        """
        room_id = self.client_rooms.pop(client_id, None)
        if not room_id:
            return None
            
        room_clients = self.rooms.get(room_id)
        if room_clients and client_id in room_clients:
            room_clients.remove(client_id)
            logger.info(f"Client {client_id} left room {room_id}")
            
            # If room is empty, clean it up
            if not room_clients:
                self.rooms.pop(room_id, None)
                logger.info(f"Room {room_id} is empty and has been removed")
            
            return room_id
        
        return None
    
    async def get_room_clients(self, room_id: str) -> Set[str]:
        """
        Get all clients in a room.
        
        Args:
            room_id: The ID of the room
            
        Returns:
            Set of client IDs in the room
        """
        return self.rooms.get(room_id, set())
    
    async def get_client_room(self, client_id: str) -> Optional[str]:
        """
        Get the room ID for a client.
        
        Args:
            client_id: The ID of the client
            
        Returns:
            The ID of the room the client is in, or None if not in any room
        """
        return self.client_rooms.get(client_id)
    
    async def room_exists(self, room_id: str) -> bool:
        """
        Check if a room exists.
        
        Args:
            room_id: The ID of the room to check
            
        Returns:
            bool: True if the room exists, False otherwise
        """
        return room_id in self.rooms
    
    async def get_room_info(self, room_id: str) -> Dict:
        """
        Get information about a room.
        
        Args:
            room_id: The ID of the room
            
        Returns:
            Dictionary containing room information
            
        Raises:
            WebSocketValidationError: If the room does not exist
        """
        if not await self.room_exists(room_id):
            raise WebSocketValidationError(f"Room {room_id} does not exist")
            
        clients = await self.get_room_clients(room_id)
        return {
            "room_id": room_id,
            "participant_count": len(clients),
            "participants": list(clients)
        }
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_client: Optional[str] = None
    ) -> None:
        """
        Broadcast a message to all clients in a room.
        
        Args:
            room_id: The ID of the room to broadcast to
            message: The message to broadcast
            exclude_client: Optional client ID to exclude from the broadcast
        """
        if room_id not in self.rooms:
            logger.warning(f"Attempted to broadcast to non-existent room: {room_id}")
            return
            
        clients = self.rooms[room_id].copy()
        if exclude_client and exclude_client in clients:
            clients.remove(exclude_client)
            
        for client_id in clients:
            try:
                await self.connection_manager.send_personal_message(message, client_id)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
    
    async def disconnect_client(self, client_id: str) -> None:
        """
        Handle client disconnection.
        
        Args:
            client_id: The ID of the disconnecting client
        """
        await self.leave_room(client_id, notify=True)
        logger.info(f"Client {client_id} disconnected")


# Global room manager instance
_room_manager = None


def get_room_manager() -> RoomManager:
    """
    Get the global room manager instance.
    
    Returns:
        RoomManager: The global room manager instance
    """
    global _room_manager
    if _room_manager is None:
        _room_manager = RoomManager()
    return _room_manager
