# app/domain/mappers/chat_mapper.py
"""
Data mapper for chat entities
"""
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from app.domain.entities.chat import ChatMessage, ChatRoom, ToolCall


class ChatDataMapper:
    """Mapper for converting between chat entities and dict representations"""

    def message_to_dict(self, message: ChatMessage) -> Dict:
        """
        Convert a ChatMessage entity to a dictionary representation
        
        Args:
            message: The chat message entity to convert
            
        Returns:
            Dictionary representation of the chat message
        """
        return {
            "id": str(message.id),
            "webtoon_id": str(message.webtoon_id),
            "client_id": message.client_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id,
            "tool_calls": [self._tool_call_to_dict(tc) for tc in message.tool_calls],
            "metadata": message.metadata,
        }
    
    def message_from_dict(self, data: Dict) -> ChatMessage:
        """
        Convert a dictionary to a ChatMessage entity
        
        Args:
            data: Dictionary representation of the chat message
            
        Returns:
            ChatMessage entity
        """
        tool_calls = [
            self._tool_call_from_dict(tc) for tc in data.get("tool_calls", [])
        ]
        
        return ChatMessage(
            id=UUID(data["id"]),
            webtoon_id=UUID(data["webtoon_id"]),
            client_id=data["client_id"],
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data["message_id"],
            tool_calls=tool_calls,
            metadata=data.get("metadata", {}),
        )
    
    def room_to_dict(self, room: ChatRoom) -> Dict:
        """
        Convert a ChatRoom entity to a dictionary representation
        
        Args:
            room: The chat room entity to convert
            
        Returns:
            Dictionary representation of the chat room
        """
        return {
            "id": str(room.id),
            "webtoon_id": str(room.webtoon_id),
            "name": room.name,
            "created_at": room.created_at.isoformat(),
            "updated_at": room.updated_at.isoformat(),
            "metadata": room.metadata,
        }
    
    def room_from_dict(self, data: Dict) -> ChatRoom:
        """
        Convert a dictionary to a ChatRoom entity
        
        Args:
            data: Dictionary representation of the chat room
            
        Returns:
            ChatRoom entity
        """
        return ChatRoom(
            id=UUID(data["id"]),
            webtoon_id=UUID(data["webtoon_id"]),
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )

    def _tool_call_to_dict(self, tool_call: ToolCall) -> Dict:
        """Convert a ToolCall entity to a dictionary"""
        return {
            "id": tool_call.id,
            "name": tool_call.name,
            "arguments": tool_call.arguments,
            "status": tool_call.status,
            "result": tool_call.result,
            "error": tool_call.error,
        }
    
    def _tool_call_from_dict(self, data: Dict) -> ToolCall:
        """Convert a dictionary to a ToolCall entity"""
        return ToolCall(
            id=data["id"],
            name=data["name"],
            arguments=data["arguments"],
            status=data["status"],
            result=data.get("result"),
            error=data.get("error"),
        )
