"""
Edge case tests for the RoomService class.

These tests cover race conditions, error handling, and other edge cases
that aren't covered by the main test suite.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.websocket.connection_manager import ConnectionManager
from app.websocket.exceptions import WebSocketError
from app.application.services.room_service import RoomService


@pytest.fixture
def mock_connection_manager():
    """Fixture providing a mock connection manager with controlled behavior."""
    manager = MagicMock(spec=ConnectionManager)
    manager.send_personal_message = AsyncMock()
    manager.broadcast = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_concurrent_join_operations(mock_connection_manager):
    """Test that concurrent join operations don't corrupt room state."""
    room_service = RoomService(connection_manager=mock_connection_manager)
    room_id = await room_service.create_room()
    
    # Number of clients to simulate
    num_clients = 10
    client_ids = [f"client-{i}" for i in range(num_clients)]
    
    # Simulate concurrent joins
    join_tasks = [
        room_service.join_room(client_id, room_id)
        for client_id in client_ids
    ]
    await asyncio.gather(*join_tasks, return_exceptions=True)
    
    # Verify all clients are in the room
    assert len(room_service.rooms[room_id]) == num_clients
    for client_id in client_ids:
        assert client_id in room_service.rooms[room_id]
        assert room_service.client_rooms[client_id] == room_id
    
    # Verify notifications were sent (n-1 notifications per client)
    # Each client should receive notifications about all other clients
    expected_notifications = (num_clients * (num_clients - 1)) // 2
    assert mock_connection_manager.send_personal_message.call_count >= expected_notifications


@pytest.mark.asyncio
async def test_notification_failure_handling():
    """Test that notification failures don't break room state."""
    # Create a mock that fails when sending to "good-client-1"
    mock_connection_manager = MagicMock(spec=ConnectionManager)
    
    async def mock_send_message(message, client_id):
        if client_id == "good-client-1":
            raise Exception("Simulated send failure")
        return None
    
    mock_connection_manager.send_personal_message.side_effect = mock_send_message
    
    # Patch the logger in the room_service module
    with patch('app.application.services.room_service.logger') as mock_logger:
        mock_logger.error = MagicMock()
        room_service = RoomService(connection_manager=mock_connection_manager)
        room_id = await room_service.create_room()
        
        # First client joins - no notifications sent
        await room_service.join_room("good-client-1", room_id)
        
        # Second client joins - should try to notify first client and fail
        await room_service.join_room("failing-client", room_id)
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Error sending message to client good-client-1" in mock_logger.error.call_args[0][0]
        
        # Verify both clients are in the room
        assert "good-client-1" in room_service.rooms[room_id]
        assert "failing-client" in room_service.rooms[room_id]


@pytest.mark.asyncio
async def test_room_cleanup_on_last_participant():
    """Test that rooms are properly cleaned up when last participant leaves."""
    room_service = RoomService()
    room_id = await room_service.create_room(metadata={"test": "data"})
    
    # Join and leave a client
    await room_service.join_room("test-client", room_id)
    await room_service.leave_room("test-client")
    
    # Verify room was cleaned up
    assert room_id not in room_service.rooms
    assert room_id not in room_service.room_metadata


@pytest.mark.asyncio
async def test_join_after_disconnect():
    """Test that a client can rejoin after disconnecting."""
    room_service = RoomService()
    room_id = await room_service.create_room()
    
    # Join and leave
    await room_service.join_room("test-client", room_id)
    await room_service.leave_room("test-client")
    
    # Create a new room for the client to join
    new_room_id = await room_service.create_room()
    
    # Should be able to join the new room
    await room_service.join_room("test-client", new_room_id)
    assert "test-client" in room_service.rooms[new_room_id]


@pytest.mark.asyncio
async def test_rapid_join_leave_cycle():
    """Test rapid join/leave cycles don't cause issues."""
    room_service = RoomService()
    room_ids = []
    
    # Test with multiple rooms to ensure no cross-contamination
    for room_num in range(3):
        room_id = await room_service.create_room()
        room_ids.append(room_id)
        
        # Join all clients first
        for i in range(5):
            client_id = f"client-{room_num}-{i}"
            await room_service.join_room(client_id, room_id)
            assert room_id in room_service.rooms
            assert client_id in room_service.rooms[room_id]
        
        # Then leave all clients
        for i in range(5):
            client_id = f"client-{room_num}-{i}"
            left_room_id = await room_service.leave_room(client_id)
            assert left_room_id == room_id
            assert client_id not in room_service.client_rooms
            
            # After the last client leaves, the room should be removed
            if i == 4:  # Last client in room
                assert room_id not in room_service.rooms
                assert room_id not in room_service.room_metadata
            else:
                # Room should still exist but with one less client
                assert room_id in room_service.rooms
                assert client_id not in room_service.rooms[room_id]
    
    # Verify all rooms were cleaned up (should have been removed when last client left)
    for room_id in room_ids:
        assert room_id not in room_service.rooms
        assert room_id not in room_service.room_metadata
    
    # Verify all clients were properly cleaned up
    assert len(room_service.client_rooms) == 0
