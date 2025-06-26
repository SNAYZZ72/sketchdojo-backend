"""
Tests for the BaseWebSocketHandler class.
"""
import asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from fastapi import WebSocket

from app.websocket.handlers.base_handler import BaseWebSocketHandler, message_handler
from app.websocket.exceptions import WebSocketValidationError
from app.websocket.connection_manager import ConnectionManager
from app.websocket.events import WebSocketEvent


class TestMessageHandlerDecorator:
    """Tests for the @message_handler decorator."""

    def test_message_handler_decorator(self):
        """Test that the decorator correctly marks handler methods."""
        # Create a test method
        async def test_method(self, client_id, message):
            pass
            
        # Apply the decorator
        decorated = message_handler("test_message")(test_method)
        
        # Check that the method was marked correctly
        assert hasattr(decorated, "_message_type")
        assert decorated._message_type == "test_message"


class TestBaseWebSocketHandler:
    """Tests for the BaseWebSocketHandler class."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create a mock ConnectionManager."""
        manager = AsyncMock(spec=ConnectionManager)
        manager.send_personal_message = AsyncMock()
        manager.broadcast = AsyncMock()
        manager.broadcast_to_room = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        websocket = AsyncMock(spec=WebSocket)
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.fixture
    def handler(self, mock_connection_manager):
        """Create a test handler instance with a mock connection manager."""
        class TestHandler(BaseWebSocketHandler):
            def __init__(self):
                super().__init__(connection_manager=mock_connection_manager)
                self._message_handlers = {"test_message": self.handle_test_message}
            
            @message_handler
            async def handle_test_message(self, client_id: str, message: Dict[str, Any], websocket: WebSocket) -> None:
                pass
                
            async def handle_error(self, client_id: str, message: Dict[str, Any], error: Exception, websocket: WebSocket = None, include_details: bool = False) -> None:
                # Override to match the expected signature
                await super().handle_error(client_id, message, error, websocket, include_details=include_details)
                
        return TestHandler()
    
    @pytest.fixture
    def handler_class(self, mock_connection_manager):
        """Create a test handler class that inherits from BaseWebSocketHandler."""
        class TestHandler(BaseWebSocketHandler):
            def __init__(self, connection_manager=None, **deps):
                super().__init__(connection_manager=connection_manager or mock_connection_manager, **deps)
                
            @message_handler("test_message")
            async def handle_test_message(self, client_id, message, websocket=None):
                await self.send_message(client_id, {"status": "received", "type": message.get("type")})
                
            @message_handler("echo")
            async def handle_echo(self, client_id, message, websocket=None):
                await self.send_message(client_id, message)
                
            async def handle_error(self, client_id: str, message: Dict[str, Any], error: Exception, websocket: WebSocket = None, include_details: bool = False) -> None:
                # Override to match the expected signature
                await super().handle_error(client_id, message, error, websocket, include_details=include_details)
                
            @message_handler("broadcast_test")
            async def handle_broadcast(self, client_id, message, websocket=None):
                await self.broadcast("test_broadcast", message_type="broadcast_message")
        
        return TestHandler
    
    @pytest.fixture
    def handler(self, handler_class, mock_connection_manager):
        """Create an instance of the test handler."""
        return handler_class(connection_manager=mock_connection_manager)
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self, handler, mock_connection_manager, mock_websocket):
        """Test handling a message with a registered handler."""
        message = {"type": "test_message", "data": "test"}
        
        await handler.handle_message("client1", message, mock_websocket)
        
        # Verify the handler was called and sent a response
        mock_connection_manager.send_personal_message.assert_awaited_once()
        args, _ = mock_connection_manager.send_personal_message.await_args
        response = args[0]
        assert response["status"] == "received"
        assert response["type"] == "test_message"
    
    @pytest.mark.asyncio
    async def test_handle_message_echo(self, handler, mock_connection_manager, mock_websocket):
        """Test the echo handler."""
        message = {"type": "echo", "data": "test echo"}
        
        await handler.handle_message("client1", message, mock_websocket)
        
        # Verify the message was echoed back
        mock_connection_manager.send_personal_message.assert_awaited_once_with(
            message, "client1"
        )
    
    @pytest.mark.asyncio
    async def test_handle_message_error(self, handler, mock_connection_manager, mock_websocket):
        """Test error handling in message handlers."""
        message = {"type": "error", "data": "should fail"}
        
        # Mock the error handler to prevent actual error handling during test
        with patch.object(handler, 'handle_error', wraps=handler.handle_error) as mock_handle_error:
            # Make sure the mock returns None to avoid NoneType errors
            mock_handle_error.return_value = None
            
            await handler.handle_message("client1", message, mock_websocket)
            
            # Verify handle_error was called
            mock_handle_error.assert_awaited_once()
            
            # Verify the error was logged (we can check the mock logger if needed)
            
    @pytest.mark.asyncio
    async def test_handle_unknown_message_type(self, handler, mock_connection_manager, mock_websocket, caplog):
        """Test handling an unknown message type."""
        message = {"type": "unknown_message_type", "data": "test"}
        
        # Mock the error handler
        mock_error_handler = AsyncMock()
        
        with patch('app.websocket.handlers.base_handler.get_error_handler', return_value=mock_error_handler):
            with caplog.at_level("DEBUG"):
                await handler.handle_message("client1", message, mock_websocket)

        # Should call the error handler with a validation error
        args, kwargs = mock_error_handler.handle_error.call_args
        assert isinstance(kwargs['error'], WebSocketValidationError)
        assert "No handler for message type" in str(kwargs['error'])
        assert kwargs['client_id'] == "client1"
        assert kwargs['websocket'] == mock_websocket
        assert kwargs['message'] == message
        assert kwargs['include_details'] is False
    
    @pytest.mark.asyncio
    async def test_broadcast(self, handler, mock_connection_manager):
        """Test the broadcast method."""
        message = {"data": "test broadcast"}
        
        await handler.broadcast(message, message_type="test_broadcast")
        
        # Verify broadcast was called with the correct message
        expected_message = {"data": "test broadcast", "type": "test_broadcast"}
        mock_connection_manager.broadcast.assert_awaited_once_with(
            expected_message, exclude_clients=set()
        )
    
    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, handler, mock_connection_manager):
        """Test broadcasting to a specific room."""
        message = {"data": "test room broadcast"}
        
        await handler.broadcast(
            message,
            room_id="room1",
            exclude_clients={"client2"},
            message_type="room_broadcast"
        )
        
        # Verify broadcast_to_room was called with the correct parameters
        expected_message = {"data": "test room broadcast", "type": "room_broadcast"}
        mock_connection_manager.broadcast_to_room.assert_awaited_once_with(
            room_id="room1",
            message=expected_message,
            exclude_clients={"client2"}
        )
    
    @pytest.mark.asyncio
    async def test_send_message_with_event(self, handler, mock_connection_manager):
        """Test sending a WebSocketEvent message."""
        from datetime import datetime, timezone
        
        class TestEvent(WebSocketEvent):
            event_type = "test_event"
            
            def __init__(self):
                super().__init__(
                    event_type="test_event",
                    data={"test": "data"},
                    timestamp=datetime.now(timezone.utc)
                )
        
        event = TestEvent()
        
        await handler.send_message("client1", event)
        
        # Verify the event was converted to a dict and sent
        mock_connection_manager.send_personal_message.assert_awaited_once()
        args, _ = mock_connection_manager.send_personal_message.await_args
        assert args[0]["type"] == "test_event"
    
    @pytest.mark.asyncio
    async def test_dependency_injection(self, mock_connection_manager):
        """Test that dependencies are correctly injected into handler methods."""
        class TestHandler(BaseWebSocketHandler):
            def __init__(self, connection_manager=None, **deps):
                super().__init__(connection_manager=connection_manager, **deps)
            
            @message_handler("with_deps")
            async def handle_with_deps(self, client_id, message, test_dep, websocket=None):
                await self.send_message(client_id, {"test_dep": test_dep})
        
        # Create handler with a test dependency
        handler = TestHandler(
            connection_manager=mock_connection_manager,
            test_dep="test_value"
        )
        
        # Call the handler
        await handler.handle_message("client1", {"type": "with_deps"})
        
        # Verify the dependency was injected and used
        mock_connection_manager.send_personal_message.assert_awaited_once_with(
            {"test_dep": "test_value"}, "client1"
        )
    
    @pytest.mark.asyncio
    async def test_handle_error(self, mock_connection_manager):
        """Test the error handler forwards to the centralized error handler."""
        # Create a test handler
        class TestErrorHandler(BaseWebSocketHandler):
            async def handle_error(self, client_id: str, message: Dict[str, Any], error: Exception, websocket: WebSocket = None, include_details: bool = False) -> None:
                # Override to match the expected signature
                await super().handle_error(client_id, message, error, websocket, include_details=include_details)

        # Create a mock websocket
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Mock the error handler
        mock_error_handler = AsyncMock()
        
        handler = TestErrorHandler(connection_manager=mock_connection_manager)
        message = {"type": "test_message"}
        error = ValueError("Test error")
        
        with patch('app.websocket.handlers.base_handler.get_error_handler', return_value=mock_error_handler):
            # Test with websocket
            await handler.handle_error(
                client_id="client1",
                message=message,
                error=error,
                websocket=mock_websocket
            )
            
            # Verify the error handler was called with the right arguments
            mock_error_handler.handle_error.assert_awaited_once()
            args, kwargs = mock_error_handler.handle_error.call_args
            assert kwargs['error'] == error
            assert kwargs['websocket'] == mock_websocket
            assert kwargs['client_id'] == "client1"
            assert kwargs['message'] == message
            assert kwargs['include_details'] is False
