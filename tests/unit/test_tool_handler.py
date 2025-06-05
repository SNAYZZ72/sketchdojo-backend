"""
Unit tests for the ToolHandler module
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.websocket.handlers.tool_handler import (
    Tool, ToolRegistry, ToolHandler, EchoTool, WeatherTool, get_tool_handler
)


class TestTool:
    """Test the base Tool class"""
    
    def test_tool_base_class(self):
        """Test the Tool base class interface"""
        # Create a concrete implementation of the abstract base class
        parameters = {
            "type": "object",
            "properties": {
                "test_param": {
                    "type": "string",
                    "description": "Test parameter"
                }
            }
        }
        
        tool = Tool(
            tool_id="test_tool",
            name="Test Tool",
            description="A test tool for unit testing",
            parameters=parameters
        )
        
        # Test properties
        assert tool.tool_id == "test_tool"
        assert tool.name == "Test Tool"
        assert tool.description == "A test tool for unit testing"
        assert tool.parameters == parameters
        
        # Test schema method
        schema = tool.to_schema()
        assert schema["tool_id"] == "test_tool"
        assert schema["name"] == "Test Tool"
        assert schema["description"] == "A test tool for unit testing"
        assert schema["parameters"] == parameters


class TestBuiltInTools:
    """Test the built-in tool implementations"""
    
    def test_echo_tool(self):
        """Test the EchoTool implementation"""
        # Create the tool
        echo_tool = EchoTool()
        
        # Test basic properties
        assert echo_tool.tool_id == "echo"
        assert echo_tool.name == "Echo"  # Not "Echo Tool" but just "Echo"
        assert "Echoes back" in echo_tool.description
        
        # Test parameters structure
        assert echo_tool.parameters["type"] == "object"
        assert "message" in echo_tool.parameters["properties"]
        assert echo_tool.parameters["required"] == ["message"]
    
    @pytest_asyncio.fixture
    async def mock_weather_data(self):
        """Mock data for weather tool testing"""
        return {
            "location": "London",
            "temperature": 22,
            "unit": "celsius",
            "condition": "sunny"
        }
    
    @pytest.mark.asyncio
    async def test_weather_tool(self, mock_weather_data):
        """Test the WeatherTool implementation"""
        # Create the tool
        weather_tool = WeatherTool()
        
        # Test basic properties
        assert weather_tool.tool_id == "weather"
        assert weather_tool.name == "Weather"
        assert "weather information" in weather_tool.description.lower()
        
        # Test parameters structure
        assert weather_tool.parameters["type"] == "object"
        assert "location" in weather_tool.parameters["properties"]
        assert weather_tool.parameters["required"] == ["location"]
        
        # Execute the tool (it uses a mock implementation)
        result = await weather_tool.execute({"location": "London"})
        assert "location" in result
        assert result["location"] == "London"
        assert "temperature" in result
        assert "condition" in result
        assert "timestamp" in result


class TestToolRegistry:
    """Test the ToolRegistry class"""
    
    def test_tool_registration(self):
        """Test registering tools"""
        registry = ToolRegistry()
        
        # Create test tools
        tool1 = Tool(
            tool_id="tool1",
            name="Tool 1",
            description="Test Tool 1",
            parameters={}
        )
        
        tool2 = Tool(
            tool_id="tool2",
            name="Tool 2",
            description="Test Tool 2",
            parameters={}
        )
        
        # Register tools
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        # Check registration
        assert len(registry.tools) == 2
        assert "tool1" in registry.tools
        assert "tool2" in registry.tools
        assert registry.get_tool("tool1") == tool1
        assert registry.get_tool("tool2") == tool2
        
        # Non-existent tool
        assert registry.get_tool("non_existent") is None
    
    def test_duplicate_tool_registration(self):
        """Test registering duplicate tools"""
        registry = ToolRegistry()
        
        # Create two tools with same ID
        tool1 = Tool(
            tool_id="duplicate",
            name="Duplicate Tool 1",
            description="First duplicate tool",
            parameters={}
        )
        
        tool2 = Tool(
            tool_id="duplicate",
            name="Duplicate Tool 2",
            description="Second duplicate tool",
            parameters={}
        )
        
        # Register first instance
        registry.register_tool(tool1)
        
        # Register second instance - should replace the first
        registry.register_tool(tool2)
        
        # Should still only have one registration
        assert len(registry.tools) == 1
        assert registry.get_tool("duplicate") == tool2


class TestToolHandler:
    """Test the ToolHandler class"""
    
    @patch("app.websocket.handlers.tool_handler.get_connection_manager")
    def test_tool_handler_initialization(self, mock_get_connection_manager):
        """Test ToolHandler initialization"""
        connection_manager = MagicMock()
        mock_get_connection_manager.return_value = connection_manager
        
        handler = ToolHandler()
        
        # Check initialization
        assert handler.connection_manager == connection_manager
        assert isinstance(handler.tool_registry, ToolRegistry)
        assert len(handler.client_permissions) == 0
    
    @patch("app.websocket.handlers.tool_handler.get_connection_manager")
    def test_permission_management(self, mock_get_connection_manager):
        """Test permission management"""
        mock_get_connection_manager.return_value = MagicMock()
        handler = ToolHandler()
        client_id = "test_client"
        
        # Grant permissions
        tools = ["echo", "weather"]
        handler.grant_permissions(client_id, tools)
        
        # Check permissions
        assert client_id in handler.client_permissions
        assert set(handler.client_permissions[client_id]) == set(tools)
        
        # Check permission validation
        assert handler.check_permission(client_id, "echo") is True
        assert handler.check_permission(client_id, "weather") is True
        assert handler.check_permission(client_id, "unknown_tool") is False
        assert handler.check_permission("unknown_client", "echo") is False
        
        # Revoke single permission
        handler.revoke_permissions(client_id, ["echo"])
        assert handler.check_permission(client_id, "echo") is False
        assert handler.check_permission(client_id, "weather") is True
        
        # Revoke all permissions
        handler.revoke_permissions(client_id)
        assert client_id not in handler.client_permissions
    
    @patch("app.websocket.handlers.tool_handler.get_connection_manager")
    def test_get_available_tools(self, mock_get_connection_manager):
        """Test getting available tools for a client"""
        mock_get_connection_manager.return_value = MagicMock()
        handler = ToolHandler()
        client_id = "test_client"
        
        # Register some tools
        echo_tool = EchoTool()
        weather_tool = WeatherTool()
        handler.register_tool(echo_tool)
        handler.register_tool(weather_tool)
        
        # No permissions yet
        available_tools = []
        for tool in handler.tool_registry.tools.values():
            if handler.check_permission(client_id, tool.tool_id):
                available_tools.append(tool)
        assert len(available_tools) == 0
        
        # Grant partial permissions
        handler.grant_permissions(client_id, ["echo"])
        
        # Test permissions
        available_tool_ids = []
        for tool in handler.tool_registry.tools.values():
            if handler.check_permission(client_id, tool.tool_id):
                available_tool_ids.append(tool.tool_id)
                
        assert len(available_tool_ids) == 1
        assert "echo" in available_tool_ids
        
        # Grant all permissions
        handler.grant_permissions(client_id, ["weather"])
        
        # Get all available tools
        available_tool_ids = []
        for tool in handler.tool_registry.tools.values():
            if handler.check_permission(client_id, tool.tool_id):
                available_tool_ids.append(tool.tool_id)
                
        assert len(available_tool_ids) == 2
        assert "echo" in available_tool_ids
        assert "weather" in available_tool_ids
    
    @pytest.mark.asyncio
    @patch("app.websocket.handlers.tool_handler.get_connection_manager")
    async def test_handle_tool_call_errors(self, mock_get_connection_manager):
        """Test handling various error conditions in tool calls"""
        connection_manager = AsyncMock()
        mock_get_connection_manager.return_value = connection_manager
        handler = ToolHandler()
        client_id = "test_client"
        
        # Setup a test tool
        echo_tool = EchoTool()
        handler.register_tool(echo_tool)
        
        # Patch the _send_tool_error method
        with patch.object(handler, '_send_tool_error') as mock_send_error:
            # Test missing tool_id
            await handler.handle_tool_call(client_id, {"call_id": "test1"})
            mock_send_error.assert_called_once()
            assert mock_send_error.call_args[0][2] == "missing_tool_id"
            mock_send_error.reset_mock()
            
            # Test non-existent tool
            await handler.handle_tool_call(client_id, {
                "call_id": "test2",
                "tool_id": "nonexistent"
            })
            mock_send_error.assert_called_once()
            assert mock_send_error.call_args[0][2] == "tool_not_found"
            mock_send_error.reset_mock()
            
            # Test permission denied
            await handler.handle_tool_call(client_id, {
                "call_id": "test3",
                "tool_id": "echo"
            })
            mock_send_error.assert_called_once()
            assert mock_send_error.call_args[0][2] == "permission_denied"
            mock_send_error.reset_mock()
            
            # Test parameter validation - missing required parameters
            handler.grant_permissions(client_id, ["echo"])
            # EchoTool requires a 'message' parameter
            await handler.handle_tool_call(client_id, {
                "call_id": "test4",
                "tool_id": "echo",
                "parameters": {}
            })
            # Check that error was called with parameter validation error
            mock_send_error.assert_called_once()
            assert mock_send_error.call_args[0][2] == "invalid_parameters"
            mock_send_error.reset_mock()


@patch("app.websocket.handlers.tool_handler.get_connection_manager")
def test_get_tool_handler(mock_get_connection_manager):
    """Test the get_tool_handler singleton function"""
    mock_get_connection_manager.return_value = MagicMock()
    
    # First call should create a new handler
    handler1 = get_tool_handler()
    assert handler1 is not None
    assert isinstance(handler1, ToolHandler)
    
    # Second call should return the same instance
    handler2 = get_tool_handler()
    assert handler2 is handler1
