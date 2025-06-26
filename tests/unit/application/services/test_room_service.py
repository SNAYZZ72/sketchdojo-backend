"""Unit tests for the RoomService class."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.application.services.room_service import RoomService, get_room_service
from app.websocket.connection_manager import ConnectionManager
from app.websocket.exceptions import WebSocketError


@pytest.fixture
def mock_connection_manager():
    """Fixture providing a mock connection manager."""
    manager = MagicMock(spec=ConnectionManager)
    manager.send_personal_message = AsyncMock()
    manager.broadcast = AsyncMock()
    return manager


@pytest.fixture
def room_service(mock_connection_manager):
    """Fixture providing a RoomService instance with a mock connection manager."""
    return RoomService(connection_manager=mock_connection_manager)


@pytest.mark.asyncio
async def test_create_room(room_service):
    """Test creating a new room."""
    room_id = await room_service.create_room()
    assert room_id is not None
    assert room_id in room_service.rooms
    assert room_id in room_service.room_metadata


@pytest.mark.asyncio
async def test_create_room_with_custom_id(room_service):
    """Test creating a room with a custom ID."""
    custom_id = "test-room-123"
    room_id = await room_service.create_room(room_id=custom_id)
    assert room_id == custom_id
    assert room_id in room_service.rooms


@pytest.mark.asyncio
async def test_create_room_with_metadata(room_service):
    """Test creating a room with metadata."""
    metadata = {"name": "Test Room", "max_participants": 10}
    room_id = await room_service.create_room(metadata=metadata)
    assert room_service.room_metadata[room_id] == metadata


@pytest.mark.asyncio
async def test_join_room(room_service, mock_connection_manager):
    """Test joining a room triggers notifications."""
    # Create room and join
    room_id = await room_service.create_room()
    client_id = "test-client-1"
    
    # Reset the mock to ignore any calls during room creation
    mock_connection_manager.send_personal_message.reset_mock()
    
    # Join the room
    await room_service.join_room(client_id, room_id)
    
    # Verify room state
    assert client_id in room_service.rooms[room_id]
    assert room_service.client_rooms[client_id] == room_id
    
    # Verify notification was sent to other participants (none in this case)
    # Since there are no other participants, no notification should be sent
    mock_connection_manager.send_personal_message.assert_not_called()
    
    # Add a second client to test notification
    client_id_2 = "test-client-2"
    await room_service.join_room(client_id_2, room_id)
    
    # Now we should have one notification sent to the first client
    mock_connection_manager.send_personal_message.assert_called_once()
    
    # Get the arguments from the call
    args, kwargs = mock_connection_manager.send_personal_message.call_args
    message = args[0]
    target_client = args[1] if len(args) > 1 else kwargs.get('client_id')
    
    # Verify the message content
    assert message["type"] == "room_update"
    assert message["event"] == "participant_joined"
    assert message["data"]["client_id"] == client_id_2
    assert message["data"]["participants"] == 2
    assert target_client == client_id  # Notification should be sent to the first client


@pytest.mark.asyncio
async def test_join_nonexistent_room(room_service):
    """Test joining a non-existent room raises an error."""
    with pytest.raises(WebSocketError) as exc_info:
        await room_service.join_room("test-client", "nonexistent-room")
    assert exc_info.value.code == "room_not_found"


@pytest.mark.asyncio
async def test_join_room_already_joined(room_service):
    """Test joining a room when already in a different room."""
    room1 = await room_service.create_room()
    room2 = await room_service.create_room()
    client_id = "test-client-1"
    
    await room_service.join_room(client_id, room1)
    
    with pytest.raises(WebSocketError) as exc_info:
        await room_service.join_room(client_id, room2)
    assert exc_info.value.code == "already_in_room"


@pytest.mark.asyncio
async def test_leave_room(room_service, mock_connection_manager):
    """Test leaving a room triggers notifications."""
    # Create room and join two clients
    room_id = await room_service.create_room()
    client_id_1 = "test-client-1"
    client_id_2 = "test-client-2"
    
    # Join first client
    await room_service.join_room(client_id_1, room_id)
    # Join second client
    await room_service.join_room(client_id_2, room_id)
    
    # Reset the mock to ignore any calls during join
    mock_connection_manager.send_personal_message.reset_mock()
    
    # First client leaves the room
    left_room_id = await room_service.leave_room(client_id_1)
    
    # Verify room state
    assert left_room_id == room_id
    assert client_id_1 not in room_service.client_rooms
    assert client_id_2 in room_service.client_rooms  # Second client should still be in the room
    
    # Verify notification was sent to remaining participants (client_2)
    mock_connection_manager.send_personal_message.assert_called_once()
    
    # Get the arguments from the call
    args, kwargs = mock_connection_manager.send_personal_message.call_args
    message = args[0]
    target_client = args[1] if len(args) > 1 else kwargs.get('client_id')
    
    # Verify the message content
    assert message["type"] == "room_update"
    assert message["event"] == "participant_left"
    assert message["data"]["client_id"] == client_id_1
    assert message["data"]["participants"] == 1  # Only client_2 remains
    assert target_client == client_id_2  # Notification should be sent to the remaining client


@pytest.mark.asyncio
async def test_leave_room_cleanup(room_service):
    """Test that empty rooms are cleaned up when last participant leaves."""
    room_id = await room_service.create_room()
    client_id = "test-client-1"
    
    await room_service.join_room(client_id, room_id)
    await room_service.leave_room(client_id)
    
    assert room_id not in room_service.rooms
    assert room_id not in room_service.room_metadata


@pytest.mark.asyncio
async def test_broadcast_to_room(room_service, mock_connection_manager):
    """Test broadcasting a message to a room."""
    room_id = await room_service.create_room()
    client1 = "client-1"
    client2 = "client-2"
    
    await room_service.join_room(client1, room_id)
    await room_service.join_room(client2, room_id)
    mock_connection_manager.send_personal_message.reset_mock()
    
    message = {"type": "test_message", "content": "Hello, world!"}
    await room_service.broadcast_to_room(room_id, message)
    
    assert mock_connection_manager.send_personal_message.call_count == 2


@pytest.mark.asyncio
async def test_broadcast_exclude_client(room_service, mock_connection_manager):
    """Test excluding a client from a broadcast."""
    room_id = await room_service.create_room()
    client1 = "client-1"
    client2 = "client-2"
    
    await room_service.join_room(client1, room_id)
    await room_service.join_room(client2, room_id)
    mock_connection_manager.send_personal_message.reset_mock()
    
    message = {"type": "test_message"}
    await room_service.broadcast_to_room(room_id, message, exclude_client=client1)
    
    # Should only send to client2
    assert mock_connection_manager.send_personal_message.call_count == 1
    args, _ = mock_connection_manager.send_personal_message.call_args
    assert args[1] == client2  # client_id is the second argument


@pytest.mark.asyncio
async def test_get_room_info(room_service):
    """Test getting room information."""
    metadata = {"name": "Test Room"}
    room_id = await room_service.create_room(metadata=metadata)
    await room_service.join_room("client-1", room_id)
    await room_service.join_room("client-2", room_id)
    
    info = await room_service.get_room_info(room_id)
    
    assert info["exists"] is True
    assert info["room_id"] == room_id
    assert info["participant_count"] == 2
    assert set(info["participants"]) == {"client-1", "client-2"}
    assert info["metadata"] == metadata


@pytest.mark.asyncio
async def test_get_nonexistent_room_info(room_service):
    """Test getting info for a non-existent room."""
    info = await room_service.get_room_info("nonexistent-room")
    assert info["exists"] is False


@pytest.mark.asyncio
async def test_get_client_room(room_service):
    """Test getting a client's current room."""
    room_id = await room_service.create_room()
    client_id = "test-client"
    
    await room_service.join_room(client_id, room_id)
    
    result = await room_service.get_client_room(client_id)
    assert result == room_id


@pytest.mark.asyncio
async def test_get_client_room_not_in_room(room_service):
    """Test getting room for client not in any room."""
    result = await room_service.get_client_room("nonexistent-client")
    assert result is None


@pytest.mark.asyncio
async def test_singleton_room_service():
    """Test that get_room_service returns a singleton instance."""
    service1 = get_room_service()
    service2 = get_room_service()
    assert service1 is service2
