"""Unit tests for the ToolHandler class."""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

from app.websocket.handlers.tool_handler import (
    ToolHandler, Tool, ToolRegistry, EchoTool, WeatherTool, get_tool_handler
)
from app.websocket.connection_manager import ConnectionManager, get_connection_manager
from app.websocket.events import (
    ToolDiscoveryEvent, ToolCallResultEvent, ToolCallErrorEvent
)

# Fixtures

@pytest.fixture
def mock_connection_manager():
    """Fixture providing a mock connection manager."""
    manager = AsyncMock(spec=ConnectionManager)
    # Add the send_json method to the mock
    manager.send_json = AsyncMock()
    manager.send_personal_message = AsyncMock()
    return manager

@pytest.fixture
def tool_handler(mock_connection_manager):
    """Fixture for creating a ToolHandler instance with a mock connection manager"""
    # Reset the singleton before each test
    from app.websocket.handlers.tool_handler import _tool_handler
    _tool_handler = None
    
    return ToolHandler(connection_manager=mock_connection_manager)

@pytest.fixture
def mock_websocket():
    """Fixture providing a mock WebSocket."""
    ws = AsyncMock(spec=WebSocket)
    return ws

# Test Tool Class

def test_tool_to_schema():
    """Test that a tool can be converted to a schema."""
    tool = Tool(
        tool_id="test_tool",
        name="Test Tool",
        description="A test tool",
        parameters={"type": "object"}
    )
    schema = tool.to_schema()
    assert schema == {
        "tool_id": "test_tool",
        "name": "Test Tool",
        "description": "A test tool",
        "parameters": {"type": "object"}
    }

# Test ToolRegistry Class

def test_tool_registry_register_tool():
    """Test registering a tool with the registry."""
    registry = ToolRegistry()
    tool = Tool("test", "Test", "A test tool", {})
    registry.register_tool(tool)
    assert registry.get_tool("test") == tool

def test_tool_registry_list_tools():
    """Test listing all tools in the registry."""
    registry = ToolRegistry()
    tool1 = Tool("test1", "Test 1", "First test tool", {})
    tool2 = Tool("test2", "Test 2", "Second test tool", {})
    registry.register_tool(tool1)
    registry.register_tool(tool2)
    tools = registry.list_tools()
    assert len(tools) == 2
    assert {t["tool_id"] for t in tools} == {"test1", "test2"}

# Test ToolHandler Class

@pytest.mark.asyncio
async def test_handle_discover_tools(tool_handler, mock_connection_manager):
    """Test handling a tool discovery request."""
    # Setup
    client_id = "test_client"
    message = {"type": "discover_tools"}

    # Grant permission for one tool
    tool = EchoTool()
    tool_handler.register_tool(tool)
    tool_handler.grant_permissions(client_id, ["echo"])

    # Add another tool without permissions
    tool_handler.register_tool(WeatherTool())

    # Execute
    await tool_handler.handle_discover_tools(client_id, message)

    # Verify
    mock_connection_manager.send_personal_message.assert_awaited_once()
    args, _ = mock_connection_manager.send_personal_message.call_args
    
    # First argument is the message, second is client_id
    message_payload = args[0]
    client_id_arg = args[1]
    
    # Check client_id is passed correctly
    assert client_id_arg == client_id
    
    # Check message structure
    assert "type" in message_payload
    assert message_payload["type"] == "tool_discovery"
    assert "client_id" in message_payload
    assert message_payload["client_id"] == client_id
    assert "tools" in message_payload
    assert isinstance(message_payload["tools"], list)
    
    # Check the echo tool is in the response
    echo_tool = next((t for t in message_payload["tools"] if t.get("tool_id") == "echo"), None)
    assert echo_tool is not None
    assert echo_tool["name"] == "Echo"

@pytest.mark.asyncio
async def test_handle_tool_call_success(tool_handler, mock_connection_manager):
    """Test successfully handling a tool call."""
    # Setup
    client_id = "test_client"
    call_id = str(uuid.uuid4())
    message = {
        "type": "tool_call",
        "tool_id": "echo",
        "call_id": call_id,
        "parameters": {"message": "test"}
    }
    
    # Register and grant permission for the tool
    tool = EchoTool()
    tool.execute = AsyncMock(return_value={"echo": "test"})
    tool_handler.register_tool(tool)
    tool_handler.grant_permissions(client_id, ["echo"])
    
    # Execute
    await tool_handler.handle_tool_call(client_id, message)
    
    # Verify
    tool.execute.assert_awaited_once_with({"message": "test"})
    mock_connection_manager.send_personal_message.assert_awaited_once()
    args, _ = mock_connection_manager.send_personal_message.call_args
    
    # The first argument is the message dict, second is client_id
    message = args[0]
    client_id_arg = args[1]
    
    # Verify client_id is passed correctly
    assert client_id_arg == client_id
    
    # Verify message structure matches ToolCallResultEvent
    assert "type" in message
    assert message["type"] == "tool_call_result"
    assert "tool_id" in message
    assert message["tool_id"] == "echo"
    assert "call_id" in message
    assert message["call_id"] == call_id
    assert "result" in message
    assert message["result"] == {"echo": "test"}

@pytest.mark.asyncio
async def test_handle_tool_call_missing_permission(tool_handler, mock_connection_manager):
    """Test handling a tool call without permission."""
    # Setup
    client_id = "test_client"
    call_id = str(uuid.uuid4())
    message = {
        "type": "tool_call",
        "tool_id": "echo",
        "call_id": call_id,
        "parameters": {"message": "test"}
    }
    
    # Register tool but don't grant permission
    tool_handler.register_tool(EchoTool())
    
    # Execute
    await tool_handler.handle_tool_call(client_id, message)
    
    # Verify error response
    mock_connection_manager.send_personal_message.assert_awaited_once()
    args, _ = mock_connection_manager.send_personal_message.call_args
    
    # The first argument is the message dict, second is client_id
    message = args[0]
    client_id_arg = args[1]
    
    # Verify client_id is passed correctly
    assert client_id_arg == client_id
    
    # Verify message structure matches ToolCallErrorEvent
    assert "type" in message
    assert message["type"] == "tool_call_error"
    assert "tool_id" in message
    assert message["tool_id"] == "echo"
    assert "call_id" in message
    assert message["call_id"] == call_id
    assert "error_code" in message
    assert message["error_code"] == "permission_denied"
    assert "error_message" in message
    assert "You don't have permission to use this tool" in message["error_message"]

# Test Built-in Tools

@pytest.mark.asyncio
async def test_echo_tool_execute():
    """Test the built-in EchoTool."""
    tool = EchoTool()
    result = await tool.execute({"message": "test"})
    assert "message" in result
    assert "echo_timestamp" in result
    assert result["message"] == "test"

@pytest.mark.asyncio
async def test_weather_tool_execute():
    """Test the built-in WeatherTool."""
    tool = WeatherTool()
    result = await tool.execute({"location": "Paris"})
    assert "location" in result
    assert "temperature" in result
    assert "condition" in result
    assert result["location"] == "Paris"

# Test Global Tool Handler

def test_get_tool_handler_singleton(monkeypatch, mock_connection_manager):
    """Test that get_tool_handler returns a singleton instance."""
    # Use monkeypatch to handle the singleton reset
    from app.websocket.handlers.tool_handler import _tool_handler
    monkeypatch.setattr('app.websocket.handlers.tool_handler._tool_handler', None)
    
    # First call should create a new instance
    handler1 = get_tool_handler(connection_manager=mock_connection_manager)
    
    # Second call should return the same instance
    handler2 = get_tool_handler()
    
    # Should be the same instance
    assert handler1 is handler2
    
    # The connection manager should be set
    assert hasattr(handler1, 'connection_manager')
    assert handler1.connection_manager is mock_connection_manager

def test_get_tool_handler_with_connection_manager(monkeypatch, mock_connection_manager):
    """Test getting tool handler with a custom connection manager."""
    # Use monkeypatch to handle the singleton reset
    monkeypatch.setattr('app.websocket.handlers.tool_handler._tool_handler', None)
    
    # Get handler with custom connection manager
    handler = get_tool_handler(connection_manager=mock_connection_manager)
    
    # The handler should have the provided connection manager
    assert hasattr(handler, 'connection_manager')
    assert handler.connection_manager is mock_connection_manager
    
    # The global instance should now be set
    from app.websocket.handlers.tool_handler import _tool_handler as global_handler
    assert global_handler is handler

# Test Error Handling

@pytest.mark.asyncio
async def test_tool_execution_error(tool_handler, mock_connection_manager):
    """Test handling of tool execution errors."""
    # Setup
    client_id = "test_client"
    call_id = str(uuid.uuid4())
    message = {
        "type": "tool_call",
        "tool_id": "echo",
        "call_id": call_id,
        "parameters": {"message": "test"}
    }
    
    # Register a tool that will raise an exception
    tool = EchoTool()
    tool.execute = AsyncMock(side_effect=Exception("Test error"))
    tool_handler.register_tool(tool)
    tool_handler.grant_permissions(client_id, ["echo"])
    
    # Execute
    await tool_handler.handle_tool_call(client_id, message)
    
    # Verify error response
    mock_connection_manager.send_personal_message.assert_awaited_once()
    args, _ = mock_connection_manager.send_personal_message.call_args
    
    # First argument is the message, second is client_id
    message_payload = args[0]
    client_id_arg = args[1]
    
    # Check client_id is passed correctly
    assert client_id_arg == client_id
    
    # Check error message structure
    assert "type" in message_payload
    assert message_payload["type"] == "tool_call_error"
    assert "error_code" in message_payload
    assert message_payload["error_code"] == "execution_error"
    assert "error_message" in message_payload
    assert "Test error" in message_payload["error_message"]
    assert "tool_id" in message_payload
    assert message_payload["tool_id"] == "echo"
    assert "call_id" in message_payload
    assert message_payload["call_id"] == call_id
