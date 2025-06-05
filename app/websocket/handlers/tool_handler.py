"""
WebSocket handler for tool call functionality
"""
import logging
import json
from typing import Any, Dict, List, Callable, Optional, Type
from datetime import datetime, UTC
from uuid import uuid4

from app.websocket.connection_manager import get_connection_manager
from app.websocket.events import ToolDiscoveryEvent, ToolCallResultEvent, ToolCallErrorEvent

logger = logging.getLogger(__name__)


class Tool:
    """Base class for tool definitions"""
    
    def __init__(self, tool_id: str, name: str, description: str, parameters: Dict[str, Any]):
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to JSON schema format for client consumption"""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the provided parameters"""
        raise NotImplementedError("Tool subclasses must implement execute method")


class ToolRegistry:
    """Registry for available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the registry"""
        self.tools[tool.tool_id] = tool
        logger.info(f"Registered tool: {tool.name} (ID: {tool.tool_id})")
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by ID"""
        return self.tools.get(tool_id)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools in schema format"""
        return [tool.to_schema() for tool in self.tools.values()]


class ToolHandler:
    """Handle tool calls from WebSocket clients"""
    
    def __init__(self):
        self.connection_manager = get_connection_manager()
        self.tool_registry = ToolRegistry()
        # Keep track of which clients have permission to use which tools
        self.client_permissions: Dict[str, List[str]] = {}  # client_id -> list of tool_ids
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for availability"""
        self.tool_registry.register_tool(tool)
    
    def grant_permissions(self, client_id: str, tool_ids: List[str]) -> None:
        """Grant tool usage permissions to a client"""
        if client_id not in self.client_permissions:
            self.client_permissions[client_id] = []
        
        for tool_id in tool_ids:
            if tool_id not in self.client_permissions[client_id]:
                self.client_permissions[client_id].append(tool_id)
    
    def revoke_permissions(self, client_id: str, tool_ids: Optional[List[str]] = None) -> None:
        """Revoke tool usage permissions from a client"""
        if client_id not in self.client_permissions:
            return
        
        if tool_ids is None:
            # Revoke all permissions
            del self.client_permissions[client_id]
        else:
            # Revoke specific permissions
            self.client_permissions[client_id] = [
                tool_id for tool_id in self.client_permissions[client_id] 
                if tool_id not in tool_ids
            ]
    
    def check_permission(self, client_id: str, tool_id: str) -> bool:
        """Check if client has permission to use the tool"""
        return (
            client_id in self.client_permissions 
            and tool_id in self.client_permissions[client_id]
        )
    
    def get_available_tools(self, client_id: str) -> List[Tool]:
        """Get available tools for a client based on permissions"""
        if client_id not in self.client_permissions:
            # By default, all clients have access to all tools
            return list(self.tool_registry.tools.values())
        
        # Filter tools based on permissions
        allowed_tools = []
        for tool_id, tool in self.tool_registry.tools.items():
            if tool_id in self.client_permissions[client_id]:
                allowed_tools.append(tool)
        return allowed_tools
    
    async def handle_tool_discovery(self, client_id: str) -> None:
        """Handle tool discovery request"""
        if not client_id:
            logger.error("Cannot discover tools: Missing client ID")
            return
        
        # Get available tools for this client
        available_tools = self.get_available_tools(client_id)
        tools_info = [tool.to_schema() for tool in available_tools]
        
        # Send tool discovery response using the event class
        event = ToolDiscoveryEvent.create(client_id, tools_info)
        await self.connection_manager.send_personal_message(event.to_dict(), client_id)
        
        logger.debug(f"Sent tool discovery response to client {client_id}")
    
    async def handle_tool_call(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle tool call request from client"""
        tool_id = message.get("tool_id")
        call_id = message.get("call_id", str(uuid4()))
        parameters = message.get("parameters", {})
        message_id = message.get("message_id")
        
        # Validate request
        if not tool_id:
            await self._send_tool_error(
                client_id, 
                call_id, 
                "missing_tool_id", 
                "Tool ID is required"
            )
            return
        
        # Check if tool exists
        tool = self.tool_registry.get_tool(tool_id)
        if not tool:
            await self._send_tool_error(
                client_id, 
                call_id, 
                "tool_not_found", 
                f"Tool with ID {tool_id} not found"
            )
            return
        
        # Check if client has permission to use the tool
        if not self.check_permission(client_id, tool_id):
            await self._send_tool_error(
                client_id, 
                call_id, 
                "permission_denied", 
                "You don't have permission to use this tool"
            )
            return
        
        try:
            # Validate parameters
            tool_schema = tool.to_schema()
            required_params = tool_schema["parameters"].get("required", [])
            for param in required_params:
                if param not in parameters:
                    await self._send_tool_error(
                        client_id, 
                        call_id, 
                        "invalid_parameters", 
                        f"Missing required parameter: {param}"
                    )
                    return
            
            # Execute tool
            logger.info(f"Client {client_id} calling tool {tool_id}")
            result = await tool.execute(parameters)
            
            # Send the result back to the client using the event class
            event = ToolCallResultEvent.create(
                client_id=client_id,
                tool_id=tool_id,
                call_id=call_id,
                result=result,
                message_id=message_id
            )
            await self.connection_manager.send_personal_message(event.to_dict(), client_id)
            
            logger.debug(f"Tool {tool_id} call completed for client {client_id}")
            
        except Exception as e:
            logger.exception(f"Error executing tool {tool_id}")
            await self._send_tool_error(
                client_id, 
                call_id, 
                "execution_error", 
                str(e)
            )
    
    async def _send_tool_error(
        self, client_id: str, call_id: str, error_code: str, error_message: str
    ) -> None:
        # Notify client of the error using the event class
        event = ToolCallErrorEvent.create(
            client_id=client_id,
            error_code=error_code,
            error_message=error_message,
            message_id=call_id
        )
        await self.connection_manager.send_personal_message(event.to_dict(), client_id)
        
        logger.error(f"Tool call error for client {client_id}: {error_code} - {error_message}")
    
    async def handle_client_disconnect(self, client_id: str) -> None:
        """Handle client disconnection"""
        self.revoke_permissions(client_id)
        logger.info(f"Revoked all tool permissions for disconnected client {client_id}")


# Example built-in tools

class EchoTool(Tool):
    """Simple echo tool for testing"""
    
    def __init__(self):
        super().__init__(
            tool_id="echo",
            name="Echo",
            description="Echoes back the input message",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo"
                    }
                },
                "required": ["message"]
            }
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        message = parameters.get("message", "")
        return {
            "message": message,
            "echo_timestamp": datetime.now(UTC).isoformat()
        }


class WeatherTool(Tool):
    """Example weather information tool"""
    
    def __init__(self):
        super().__init__(
            tool_id="weather",
            name="Weather",
            description="Get weather information for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or location name"
                    }
                },
                "required": ["location"]
            }
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # This is a mock implementation
        location = parameters.get("location", "")
        
        # In a real implementation, this would call a weather API
        return {
            "location": location,
            "temperature": 22,
            "unit": "celsius",
            "condition": "sunny",
            "timestamp": datetime.now(UTC).isoformat()
        }


# Global tool handler instance
_tool_handler = None


def get_tool_handler() -> ToolHandler:
    """Get the global tool handler instance"""
    global _tool_handler
    if _tool_handler is None:
        _tool_handler = ToolHandler()
        
        # Register built-in tools
        _tool_handler.register_tool(EchoTool())
        _tool_handler.register_tool(WeatherTool())
        
    return _tool_handler
