"""
Tests for the WebSocketErrorHandler class.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket

from app.websocket.error_handler_v2 import WebSocketErrorHandler
from app.websocket.exceptions import WebSocketError, WebSocketValidationError


class TestWebSocketErrorHandler:
    """Tests for WebSocketErrorHandler functionality."""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Create a mock connection manager."""
        manager = MagicMock()
        manager.send_personal_message = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = AsyncMock(spec=WebSocket)
        return ws
    
    @pytest.fixture
    def handler(self, mock_connection_manager):
        """Create a test WebSocket error handler."""
        return WebSocketErrorHandler(connection_manager=mock_connection_manager)
    
    @pytest.mark.asyncio
    async def test_handle_error_with_websocket(self, handler, mock_websocket):
        """Test handling an error with a WebSocket connection."""
        error = WebSocketError("Test error")
        
        # Create a mock for the send_error function
        with patch('app.websocket.error_handler_v2.send_error') as mock_send_error:
            # Configure the mock to return None (since it's an async function)
            mock_send_error.return_value = None
            
            # Execute the test
            await handler.handle_error(error, context={"websocket": mock_websocket})
            
            # Verify send_error was called correctly
            mock_send_error.assert_awaited_once()
            args, kwargs = mock_send_error.await_args
            
            # Check the arguments passed to send_error
            assert args[0] is mock_websocket
            assert isinstance(args[1], WebSocketError)
            assert str(args[1]) == "Test error"
    
    @pytest.mark.asyncio
    async def test_handle_error_with_client_id(self, handler, mock_connection_manager):
        """Test handling an error with a client ID."""
        error = WebSocketError("Test error")
        
        await handler.handle_error(error, context={"client_id": "test-client"})
        
        mock_connection_manager.send_personal_message.assert_awaited_once()
        
        # Check that the message contains our error
        message = mock_connection_manager.send_personal_message.await_args[0][0]
        assert message["type"] == "error"
        assert message["code"] == "websocket_error"
        assert message["message"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_wrap_async_handler_success(self, handler, mock_websocket):
        """Test wrapping an async handler that succeeds."""
        mock_handler = AsyncMock(return_value="success")
        
        wrapped = handler.wrap_async_handler(mock_handler)
        result = await wrapped(websocket=mock_websocket, client_id="test-client")
        
        assert result == "success"
        mock_handler.assert_awaited_once_with(websocket=mock_websocket, client_id="test-client")
    
    @pytest.mark.asyncio
    async def test_wrap_async_handler_error(self, handler, mock_websocket, mock_connection_manager):
        """Test wrapping an async handler that raises an error."""
        error = WebSocketValidationError("Validation failed", {"field": "required"})
        mock_handler = AsyncMock(side_effect=error)
        
        # Configure the connection manager's send_personal_message mock
        mock_connection_manager.send_personal_message = AsyncMock(return_value=None)
        
        # Create a mock for the format_error function
        with patch('app.websocket.exceptions.format_error') as mock_format_error:
            # Configure the mock to return a formatted error message
            mock_format_error.return_value = {
                "type": "error",
                "code": "validation_error",
                "message": "Validation failed"
            }
            
            # Wrap the handler and execute it
            wrapped = handler.wrap_async_handler(mock_handler)
            result = await wrapped(
                websocket=mock_websocket,
                client_id="test-client",
                message={"type": "test"}
            )
            
            # Verify the result is None (error was caught)
            assert result is None
            
            # Verify the error was sent to the client
            mock_connection_manager.send_personal_message.assert_awaited_once()
            
            # Check the error message that was sent
            message = mock_connection_manager.send_personal_message.await_args[0][0]
            assert message["type"] == "error"
            assert message["code"] == "validation_error"
            assert message["message"] == "Validation failed"
    
    @pytest.mark.asyncio
    async def test_decorator_syntax(self, handler, mock_websocket):
        """Test using the handler as a decorator."""
        @handler()
        async def test_handler(websocket: WebSocket, message: dict):
            return "success"
            
        result = await test_handler(websocket=mock_websocket, message={"type": "test"})
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_extract_context_from_args(self, handler, mock_websocket):
        """Test extracting context from handler arguments."""
        # Test with WebSocket in args
        context = handler._get_context_from_args((mock_websocket,), {})
        assert context["websocket"] is mock_websocket
        
        # Test with client_id in kwargs
        context = handler._get_context_from_args((), {"client_id": "test-client"})
        assert context["client_id"] == "test-client"
        
        # Test with message in kwargs
        test_message = {"type": "test", "data": "test"}
        context = handler._get_context_from_args((), {"message": test_message})
        assert context["message"] == test_message
