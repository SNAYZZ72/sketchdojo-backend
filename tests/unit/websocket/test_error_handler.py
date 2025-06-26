"""
Tests for WebSocket error handler.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket

from app.websocket.error_handler import WebSocketErrorHandler, get_error_handler
from app.websocket.exceptions import (
    WebSocketError,
    WebSocketValidationError,
    WebSocketInternalError
)
from app.websocket.connection_manager import ConnectionManager


class TestWebSocketErrorHandler:
    """Tests for the WebSocketErrorHandler class."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create a mock connection manager."""
        return AsyncMock(spec=ConnectionManager)
    
    @pytest.fixture
    def error_handler(self, mock_connection_manager):
        """Create an error handler with a mock connection manager."""
        return WebSocketErrorHandler(connection_manager=mock_connection_manager)
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        return AsyncMock(spec=WebSocket)
    
    @pytest.mark.asyncio
    async def test_handle_error_with_websocket(self, error_handler, mock_websocket):
        """Test handling an error with a WebSocket connection."""
        error = WebSocketValidationError("Test error")
        
        await error_handler.handle_error(
            error=error,
            websocket=mock_websocket,
            client_id="test-client",
            message={"type": "test_message"}
        )
        
        # Verify the error was sent through the WebSocket
        mock_websocket.send_json.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_handle_error_with_client_id(self, error_handler, mock_connection_manager):
        """Test handling an error with just a client ID."""
        error = WebSocketValidationError("Test error")
        
        await error_handler.handle_error(
            error=error,
            client_id="test-client"
        )
        
        # Verify the error was sent through the connection manager
        mock_connection_manager.send_personal_message.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_wrap_async_handler_success(self, error_handler):
        """Test wrapping an async handler that succeeds."""
        async def test_handler(a: int, b: int) -> int:
            return a + b
            
        wrapped = error_handler.wrap_async_handler(test_handler)
        result = await wrapped(a=2, b=3)
        
        assert result == 5
        
    @pytest.mark.asyncio
    async def test_wrap_async_handler_error(self, error_handler, mock_websocket):
        """Test wrapping an async handler that raises an error."""
        error = WebSocketValidationError("Test error")
        
        async def test_handler():
            raise error
            
        wrapped = error_handler.wrap_async_handler(test_handler)
        result = await wrapped(
            websocket=mock_websocket,
            client_id="test-client",
            message={"type": "test_message"}
        )
        
        assert result is None
        mock_websocket.send_json.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_decorator_syntax(self, error_handler, mock_websocket):
        """Test using the error handler as a decorator."""
        error = WebSocketValidationError("Test error")
        
        @error_handler()
        async def test_handler():
            raise error
            
        result = await test_handler(
            websocket=mock_websocket,
            client_id="test-client",
            message={"type": "test_message"}
        )
        
        assert result is None
        mock_websocket.send_json.assert_awaited_once()


class TestGetErrorHandler:
    """Tests for the get_error_handler function."""
    
    def test_get_error_handler_returns_singleton(self):
        """Test that get_error_handler returns the same instance."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2
