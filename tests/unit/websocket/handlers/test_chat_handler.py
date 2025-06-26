"""
Unit tests for the ChatHandler class.
"""
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from fastapi import WebSocket

from app.websocket.handlers.chat_handler import ChatHandler
from app.websocket.connection_manager import ConnectionManager
from app.websocket.exceptions import WebSocketValidationError


@pytest.fixture
def mock_connection_manager():
    """Fixture for a mock connection manager."""
    manager = AsyncMock(spec=ConnectionManager)
    manager.send_personal_message = AsyncMock()
    return manager


@pytest.fixture
def mock_room_manager():
    """Fixture for a mock room manager."""
    manager = AsyncMock()
    manager.join_room = AsyncMock()
    manager.leave_room = AsyncMock(return_value="test_room")
    manager.get_client_room = AsyncMock(return_value=None)
    manager.get_room_info = AsyncMock(return_value={"participant_count": 1, "participants": ["test_client"]})
    manager.broadcast_to_room = AsyncMock()
    return manager


@pytest.fixture
def chat_handler(mock_connection_manager, mock_room_manager):
    """Fixture for a ChatHandler instance with mock dependencies."""
    return ChatHandler(
        connection_manager=mock_connection_manager,
        room_manager=mock_room_manager
    )


@pytest.mark.asyncio
async def test_handle_join_room_success(chat_handler, mock_connection_manager, mock_room_manager):
    """Test successfully joining a room."""
    client_id = "test_client"
    room_id = str(uuid.uuid4())
    message = {"type": "join_room", "room_id": room_id}
    
    # Mock WebSocket
    mock_websocket = MagicMock(spec=WebSocket)
    mock_websocket.send_text = AsyncMock()
    
    # Setup mock room manager
    mock_room_manager.join_room = AsyncMock()
    mock_room_manager.get_room_info.return_value = {
        "participant_count": 1,
        "participants": [client_id]
    }
    
    # Call the handler
    await chat_handler.handle_join_room(client_id, message, mock_websocket)
    
    # Verify the room manager was called correctly
    mock_room_manager.join_room.assert_awaited_once_with(
        client_id, room_id, mock_websocket
    )
    
    # Verify the success message was sent
    mock_connection_manager.send_personal_message.assert_awaited_once()
    sent_message = mock_connection_manager.send_personal_message.await_args[0][0]
    assert sent_message["type"] == "chat_room_joined"
    assert sent_message["room_id"] == room_id
    assert sent_message["participants"] == 1


@pytest.mark.asyncio
async def test_handle_join_room_missing_room_id(chat_handler, mock_connection_manager):
    """Test joining a room with a missing room_id."""
    client_id = "test_client"
    message = {"type": "join_room"}  # Missing room_id

    # Mock WebSocket
    mock_websocket = AsyncMock(spec=WebSocket)
    
    # Mock the error handler
    mock_error_handler = AsyncMock()
    
    # Call the handler with the mocked error handler
    with patch('app.websocket.handlers.base_handler.get_error_handler', return_value=mock_error_handler):
        await chat_handler.handle_join_room(client_id, message, mock_websocket)
    
    # Verify the error handler was called with the right arguments
    mock_error_handler.handle_error.assert_awaited_once()
    args, kwargs = mock_error_handler.handle_error.call_args
    assert isinstance(kwargs['error'], WebSocketValidationError)
    assert "room_id is required" in str(kwargs['error'])
    assert kwargs['websocket'] == mock_websocket
    assert kwargs['client_id'] == client_id
    assert kwargs['message'] == message
    assert kwargs['include_details'] is False


@pytest.mark.asyncio
async def test_handle_leave_room(chat_handler, mock_connection_manager, mock_room_manager):
    """Test leaving a room."""
    client_id = "test_client"
    room_id = "test_room"
    
    # Setup mock room manager
    mock_room_manager.get_client_room.return_value = room_id
    mock_room_manager.leave_room.return_value = room_id
    mock_room_manager.get_room_info.return_value = {
        "participant_count": 0,
        "participants": []
    }
    
    # Call the handler
    message = {"type": "leave_room"}
    await chat_handler.handle_leave_room(client_id, message)
    
    # Verify the room manager was called correctly
    mock_room_manager.leave_room.assert_awaited_once_with(client_id)
    
    # Verify the leave notification was broadcast
    mock_room_manager.broadcast_to_room.assert_awaited_once()
    broadcast_args = mock_room_manager.broadcast_to_room.await_args[0]
    assert broadcast_args[0] == room_id
    assert broadcast_args[1]["type"] == "participant_left"


@pytest.mark.asyncio
async def test_handle_chat_message(chat_handler, mock_connection_manager, mock_room_manager):
    """Test handling a chat message."""
    client_id = "test_client"
    room_id = "test_room"
    
    # Setup mock room manager
    mock_room_manager.get_client_room.return_value = room_id
    mock_room_manager.get_room_info.return_value = {
        "participant_count": 2,
        "participants": [client_id, "other_client"]
    }
    
    # Prepare message
    message = {
        "type": "chat_message",
        "text": "Hello, world!",
        "role": "user"
    }
    
    # Call the handler
    await chat_handler.handle_chat_message(client_id, message)
    
    # Verify the message was broadcast to all room participants
    mock_room_manager.broadcast_to_room.assert_awaited_once()
    broadcast_args = mock_room_manager.broadcast_to_room.await_args[0]
    assert broadcast_args[0] == room_id
    assert broadcast_args[1]["type"] == "chat_message"


@pytest.mark.asyncio
async def test_handle_typing_indicator(chat_handler, mock_connection_manager, mock_room_manager):
    """Test handling a typing indicator."""
    client_id = "test_client"
    room_id = "test_room"
    
    # Setup mock room manager
    mock_room_manager.get_client_room.return_value = room_id
    
    # Prepare message
    message = {
        "type": "typing_indicator",
        "is_typing": True
    }
    
    # Call the handler
    await chat_handler.handle_typing_indicator(client_id, message)
    
    # Verify the typing indicator was broadcast to other participants
    mock_room_manager.broadcast_to_room.assert_awaited_once()
    broadcast_args = mock_room_manager.broadcast_to_room.await_args[0]
    assert broadcast_args[0] == room_id
    assert broadcast_args[1]["type"] == "typing_indicator"
    assert broadcast_args[1]["client_id"] == client_id
    assert broadcast_args[1]["is_typing"] is True


@pytest.mark.asyncio
async def test_handle_client_disconnect(chat_handler, mock_connection_manager, mock_room_manager):
    """Test handling client disconnection."""
    client_id = "test_client"
    room_id = "test_room"
    
    # Setup mock room manager
    mock_room_manager.get_client_room.return_value = room_id
    mock_room_manager.leave_room.return_value = room_id
    mock_room_manager.get_room_info.return_value = {
        "participant_count": 1,
        "participants": ["other_client"]
    }
    
    # Mock the tool handler
    with patch("app.websocket.handlers.chat_handler.get_tool_handler") as mock_get_tool_handler:
        mock_tool_handler = AsyncMock()
        mock_get_tool_handler.return_value = mock_tool_handler
        
        # Call the handler
        await chat_handler.handle_client_disconnect(client_id)
        
        # Verify the room manager was called correctly
        mock_room_manager.leave_room.assert_awaited_once_with(client_id)
        
        # Verify the tool handler was notified
        mock_tool_handler.handle_client_disconnect.assert_awaited_once_with(client_id)
        
        # Verify other participants were notified
        mock_room_manager.broadcast_to_room.assert_awaited_once()
        broadcast_args = mock_room_manager.broadcast_to_room.await_args[0]
        assert broadcast_args[0] == room_id
        assert broadcast_args[1]["type"] == "participant_left"
        assert broadcast_args[1]["client_id"] == client_id
