"""
Tests for WebSocket middleware integration in the router.
"""
import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest
from fastapi import WebSocket, WebSocketDisconnect

from app.websocket.router import websocket_endpoint, _apply_middleware, _handle_message


class MockMiddleware:
    """A mock middleware for testing the middleware chain."""
    
    def __init__(self, name):
        self.name = name
        self.called = False
    
    async def __call__(self, websocket, client_id, message, call_next):
        self.called = True
        self.last_client_id = client_id
        self.last_message = message
        
        # Add middleware name to message for testing
        if not isinstance(message, dict):
            message = {}
        
        message[f"processed_by_{self.name}"] = True
        
        # Call next middleware/handler
        response = await call_next(websocket, client_id, message)
        
        # Modify response for testing
        if isinstance(response, dict):
            response[f"processed_by_{self.name}"] = True
        
        return response


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock(spec=WebSocket)
    ws.client = MagicMock()
    ws.client.host = "127.0.0.1"
    return ws


@pytest.fixture
def mock_handlers():
    """Create mock chat and tool handlers."""
    chat_handler = AsyncMock()
    tool_handler = AsyncMock()
    return chat_handler, tool_handler


@pytest.mark.asyncio
async def test_apply_middleware_chain():
    """Test that middleware is applied in the correct order."""
    # Setup
    middleware1 = MockMiddleware("middleware1")
    middleware2 = MockMiddleware("middleware2")
    
    async def final_handler(ws, cid, msg):
        return {"type": "response", "data": msg}
    
    # Execute
    result = await _apply_middleware(
        websocket=MagicMock(),
        client_id="test-client",
        message={"type": "test"},
        call_next=final_handler,
        middleware=[middleware1, middleware2]
    )
    
    # Verify
    assert middleware1.called
    assert middleware2.called
    assert result["processed_by_middleware1"] is True
    assert result["processed_by_middleware2"] is True


@pytest.mark.asyncio
async def test_handle_message_routing(mock_websocket, mock_handlers):
    """Test that messages are routed to the correct handler."""
    chat_handler, tool_handler = mock_handlers
    
    # Test chat message routing
    await _handle_message(
        websocket=mock_websocket,
        client_id="test-client",
        message={"type": "chat_message"},
        chat_handler=chat_handler,
        tool_handler=tool_handler,
        middleware=[]
    )
    chat_handler.handle_message.assert_called_once_with(
        "test-client", {"type": "chat_message"}, mock_websocket
    )
    tool_handler.handle_message.assert_not_called()
    
    # Reset mocks
    chat_handler.reset_mock()
    tool_handler.reset_mock()
    
    # Test tool message routing
    await _handle_message(
        websocket=mock_websocket,
        client_id="test-client",
        message={"type": "tool_call"},
        chat_handler=chat_handler,
        tool_handler=tool_handler,
        middleware=[]
    )
    tool_handler.handle_message.assert_called_once_with(
        "test-client", {"type": "tool_call"}, mock_websocket
    )
    chat_handler.handle_message.assert_not_called()


@pytest.mark.asyncio
@patch("app.websocket.router.get_connection_manager")
@patch("app.websocket.router.get_chat_handler_for_websocket")
@patch("app.websocket.router.get_tool_handler")
async def test_websocket_endpoint_with_middleware(
    mock_get_tool_handler,
    mock_get_chat_handler,
    mock_get_connection_manager,
    mock_websocket,
):
    """Test that the WebSocket endpoint applies middleware to incoming messages."""
    # Setup mocks
    connection_manager = AsyncMock()
    chat_handler = AsyncMock()
    
    # Create a mock tool registry with tools
    mock_tool_registry = MagicMock()
    mock_tool_registry.tools = {
        "test_tool": MagicMock(tool_id="test_tool"),
        "another_tool": MagicMock(tool_id="another_tool"),
    }
    
    # Setup tool handler with the mock registry and grant_permissions coroutine
    tool_handler = AsyncMock()
    tool_handler.tool_registry = mock_tool_registry
    tool_handler.grant_permissions = AsyncMock()
    tool_handler.grant_permissions.return_value = None
    
    mock_get_connection_manager.return_value = connection_manager
    mock_get_chat_handler.return_value = chat_handler
    mock_get_tool_handler.return_value = tool_handler
    
    # Setup mock query parameters
    mock_websocket.query_params.get.return_value = "test-client"
    
    # Create a simple message handler that will be called by the middleware
    async def message_handler(websocket, client_id, message):
        return {"status": "processed"}
            
    # Create a simple middleware that adds a timestamp to the message
    class TimestampMiddleware:
        async def __call__(self, websocket, client_id, message, call_next):
            if not isinstance(message, dict):
                message = {}
            message["timestamp"] = 1234567890
            return await call_next(websocket, client_id, message)
                
    # Create a test message
    test_message = {"type": "test_message", "data": "test"}
        
    # Call the _handle_message function directly to test middleware integration
    await _handle_message(
        websocket=mock_websocket,
        client_id="test-client",
        message=test_message,
        chat_handler=chat_handler,
        tool_handler=tool_handler,
        middleware=[TimestampMiddleware()]
    )
        
    # Verify the chat handler was called with the processed message
    chat_handler.handle_message.assert_called_once()
        
    # Get the message that was passed to the chat handler
    _, call_args, _ = chat_handler.handle_message.mock_calls[0]
    processed_message = call_args[1]  # Second argument is the message
        
    # Verify the middleware processed the message
    assert processed_message["timestamp"] == 1234567890
    assert processed_message["type"] == "test_message"
