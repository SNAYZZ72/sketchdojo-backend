"""
Tests for the RoomManager class.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.websocket.room_manager import RoomManager
from app.websocket.exceptions import WebSocketValidationError


@pytest.fixture
def mock_connection_manager():
    """Mock ConnectionManager for testing."""
    manager = AsyncMock()
    manager.send_personal_message = AsyncMock()
    return manager


@pytest.fixture
def room_manager(mock_connection_manager):
    """Create a RoomManager instance with a mock connection manager."""
    return RoomManager(connection_manager=mock_connection_manager)


@pytest.mark.asyncio
async def test_create_room(room_manager):
    """Test creating a new room."""
    room_id = await room_manager.create_room()
    assert isinstance(room_id, str)
    assert room_id in room_manager.rooms
    assert len(room_manager.rooms[room_id]) == 0


@pytest.mark.asyncio
async def test_join_room_success(room_manager):
    """Test successfully joining a room."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    
    result = await room_manager.join_room(client_id, room_id)
    assert result is True
    assert client_id in room_manager.rooms[room_id]
    assert room_manager.client_rooms[client_id] == room_id


@pytest.mark.asyncio
async def test_join_nonexistent_room(room_manager):
    """Test joining a non-existent room raises an error."""
    with pytest.raises(WebSocketValidationError):
        await room_manager.join_room("test_client", "nonexistent_room")


@pytest.mark.asyncio
async def test_leave_room(room_manager):
    """Test leaving a room."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    await room_manager.join_room(client_id, room_id)
    
    # Verify client is in the room
    assert client_id in room_manager.client_rooms
    assert client_id in room_manager.rooms[room_id]
    
    # Leave the room
    left_room_id = await room_manager.leave_room(client_id)
    
    # Verify room was returned and client was removed
    assert left_room_id == room_id
    assert client_id not in room_manager.client_rooms
    
    # Verify room was removed since it's now empty
    assert room_id not in room_manager.rooms


@pytest.mark.asyncio
async def test_leave_nonexistent_room(room_manager):
    """Test leaving when not in any room."""
    left_room_id = await room_manager.leave_room("nonexistent_client")
    assert left_room_id is None


@pytest.mark.asyncio
async def test_room_cleanup_on_last_participant(room_manager):
    """Test room is cleaned up when last participant leaves."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    
    await room_manager.join_room(client_id, room_id)
    assert room_id in room_manager.rooms
    
    await room_manager.leave_room(client_id)
    assert room_id not in room_manager.rooms


@pytest.mark.asyncio
async def test_get_room_clients(room_manager):
    """Test getting clients in a room."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    
    await room_manager.join_room(client_id, room_id)
    clients = await room_manager.get_room_clients(room_id)
    
    assert isinstance(clients, set)
    assert client_id in clients


@pytest.mark.asyncio
async def test_get_client_room(room_manager):
    """Test getting the room of a client."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    
    await room_manager.join_room(client_id, room_id)
    result_room_id = await room_manager.get_client_room(client_id)
    
    assert result_room_id == room_id


@pytest.mark.asyncio
async def test_room_exists(room_manager):
    """Test checking if a room exists."""
    room_id = await room_manager.create_room()
    
    assert await room_manager.room_exists(room_id) is True
    assert await room_manager.room_exists("nonexistent_room") is False


@pytest.mark.asyncio
async def test_get_room_info(room_manager):
    """Test getting room information."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    await room_manager.join_room(client_id, room_id)
    
    info = await room_manager.get_room_info(room_id)
    
    assert info["room_id"] == room_id
    assert info["participant_count"] == 1
    assert client_id in info["participants"]


@pytest.mark.asyncio
async def test_broadcast_to_room(room_manager, mock_connection_manager):
    """Test broadcasting a message to a room."""
    room_id = await room_manager.create_room()
    client1 = "client1"
    client2 = "client2"
    
    await room_manager.join_room(client1, room_id)
    await room_manager.join_room(client2, room_id)
    
    message = {"type": "test_message", "content": "Hello"}
    await room_manager.broadcast_to_room(room_id, message)
    
    # Should send to both clients
    assert mock_connection_manager.send_personal_message.await_count == 2


@pytest.mark.asyncio
async def test_broadcast_exclude_client(room_manager, mock_connection_manager):
    """Test broadcasting with an excluded client."""
    room_id = await room_manager.create_room()
    client1 = "client1"
    client2 = "client2"
    
    await room_manager.join_room(client1, room_id)
    await room_manager.join_room(client2, room_id)
    
    message = {"type": "test_message", "content": "Hello"}
    await room_manager.broadcast_to_room(room_id, message, exclude_client=client1)
    
    # Should only send to client2
    assert mock_connection_manager.send_personal_message.await_count == 1


@pytest.mark.asyncio
async def test_disconnect_client(room_manager):
    """Test disconnecting a client."""
    room_id = await room_manager.create_room()
    client_id = "test_client"
    
    await room_manager.join_room(client_id, room_id)
    await room_manager.disconnect_client(client_id)
    
    assert client_id not in room_manager.client_rooms
    assert client_id not in room_manager.rooms.get(room_id, set())


def test_get_room_manager_singleton():
    """Test that get_room_manager returns a singleton instance."""
    from app.websocket.room_manager import get_room_manager
    
    manager1 = get_room_manager()
    manager2 = get_room_manager()
    
    assert manager1 is manager2
