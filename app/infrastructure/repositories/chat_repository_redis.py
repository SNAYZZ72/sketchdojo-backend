# app/infrastructure/repositories/chat_repository_redis.py
"""
Redis implementation of the ChatRepository
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.chat import ChatMessage, ChatRoom, ToolCall
from app.domain.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)


class ChatRepositoryRedis(ChatRepository):
    """Redis implementation of the ChatRepository"""

    def __init__(self, storage: StorageProvider):
        self.storage = storage
        self.message_key_prefix = "chat:message:"
        self.room_key_prefix = "chat:room:"
        self.webtoon_messages_prefix = "chat:webtoon:"
        logger.info("ChatRepositoryRedis initialized")

    def _get_message_key(self, entity_id: UUID) -> str:
        """Get storage key for message entity ID"""
        return f"{self.message_key_prefix}{str(entity_id)}"
    
    def _get_room_key(self, entity_id: UUID) -> str:
        """Get storage key for room entity ID"""
        return f"{self.room_key_prefix}{str(entity_id)}"
    
    def _get_webtoon_messages_key(self, webtoon_id: UUID) -> str:
        """Get storage key for webtoon messages list"""
        return f"{self.webtoon_messages_prefix}{str(webtoon_id)}:messages"

    def _serialize_message(self, message: ChatMessage) -> dict:
        """Serialize chat message entity to dictionary"""
        return {
            "id": str(message.id),
            "webtoon_id": str(message.webtoon_id),
            "client_id": message.client_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "message_id": message.message_id,
            "tool_calls": [self._serialize_tool_call(tc) for tc in message.tool_calls],
            "metadata": message.metadata,
        }
    
    def _serialize_tool_call(self, tool_call: ToolCall) -> dict:
        """Serialize tool call to dictionary"""
        return {
            "id": tool_call.id,
            "name": tool_call.name,
            "arguments": tool_call.arguments,
            "status": tool_call.status,
            "result": tool_call.result,
            "error": tool_call.error,
        }
    
    def _serialize_room(self, room: ChatRoom) -> dict:
        """Serialize chat room entity to dictionary"""
        return {
            "id": str(room.id),
            "webtoon_id": str(room.webtoon_id),
            "name": room.name,
            "created_at": room.created_at.isoformat(),
            "updated_at": room.updated_at.isoformat(),
            "metadata": room.metadata,
        }

    def _deserialize_message(self, data: dict) -> ChatMessage:
        """Deserialize dictionary to chat message entity"""
        tool_calls = [
            ToolCall(
                id=tc["id"],
                name=tc["name"],
                arguments=tc["arguments"],
                status=tc["status"],
                result=tc["result"],
                error=tc["error"],
            )
            for tc in data.get("tool_calls", [])
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
    
    def _deserialize_room(self, data: dict) -> ChatRoom:
        """Deserialize dictionary to chat room entity"""
        return ChatRoom(
            id=UUID(data["id"]),
            webtoon_id=UUID(data["webtoon_id"]),
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )

    async def create(self, entity: ChatMessage) -> ChatMessage:
        """Create a new chat message"""
        # Serialize the entity
        data = self._serialize_message(entity)
        
        # Save message data
        message_key = self._get_message_key(entity.id)
        await self.storage.set(message_key, json.dumps(data))
        
        # Add message ID to webtoon messages list
        webtoon_messages_key = self._get_webtoon_messages_key(entity.webtoon_id)
        await self.storage.append_to_list(webtoon_messages_key, str(entity.id))
        
        logger.info(f"Created chat message with ID {entity.id}")
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[ChatMessage]:
        """Get chat message by ID"""
        message_key = self._get_message_key(entity_id)
        data = await self.storage.get(message_key)
        
        if not data:
            return None
            
        try:
            # Check if data is already a dictionary
            if isinstance(data, dict):
                return self._deserialize_message(data)
            else:
                # If it's a string, deserialize it
                data_dict = json.loads(data)
                return self._deserialize_message(data_dict)
        except Exception as e:
            logger.error(f"Failed to deserialize chat message {entity_id}: {str(e)}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[ChatMessage]:
        """Get all chat messages with optional filtering"""
        # This is a simplified implementation that doesn't support filtering
        # In a real implementation, we would use Redis search or other mechanisms
        webtoon_id = filters.get("webtoon_id")
        if webtoon_id:
            return await self.get_by_webtoon_id(webtoon_id, limit, skip)
            
        return []  # Not implementing full get_all to avoid loading all messages

    async def update(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[ChatMessage]:
        """Update a chat message"""
        # Get existing message
        message = await self.get_by_id(entity_id)
        if not message:
            return None
            
        # Update fields
        for key, value in data.items():
            if hasattr(message, key):
                setattr(message, key, value)
                
        # Update timestamp
        message.metadata["updated_at"] = datetime.now(UTC).isoformat()
        
        # Save updated message
        message_key = self._get_message_key(entity_id)
        await self.storage.set(message_key, json.dumps(self._serialize_message(message)))
        
        return message

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a chat message"""
        message = await self.get_by_id(entity_id)
        if not message:
            return False
            
        # Remove from webtoon messages list
        webtoon_messages_key = self._get_webtoon_messages_key(message.webtoon_id)
        await self.storage.remove_from_list(webtoon_messages_key, str(entity_id))
        
        # Delete the message
        message_key = self._get_message_key(entity_id)
        success = await self.storage.delete(message_key)
        
        return success

    async def get_by_webtoon_id(self, webtoon_id: UUID, limit: int = 100, skip: int = 0) -> List[ChatMessage]:
        """Get chat messages for a specific webtoon"""
        # Get list of message IDs for this webtoon
        webtoon_messages_key = self._get_webtoon_messages_key(webtoon_id)
        message_ids = await self.storage.get_list(webtoon_messages_key)
        
        if not message_ids:
            return []
            
        # Apply pagination
        paginated_ids = message_ids[skip:skip + limit]
        
        # Get messages by IDs
        messages = []
        for message_id in paginated_ids:
            message = await self.get_by_id(UUID(message_id))
            if message:
                messages.append(message)
                
        # Sort by timestamp (newest first)
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        
        return messages
    
    async def get_chat_room_by_webtoon_id(self, webtoon_id: UUID) -> Optional[ChatRoom]:
        """Get chat room for a specific webtoon"""
        # For this implementation, we'll use a consistent room ID based on the webtoon ID
        # In a more complex implementation, we might store room mappings
        room_key = self._get_room_key(webtoon_id)
        data_str = await self.storage.get(room_key)
        
        if data_str:
            try:
                data = json.loads(data_str)
                return self._deserialize_room(data)
            except Exception as e:
                logger.error(f"Failed to deserialize chat room for webtoon {webtoon_id}: {str(e)}")
                
        # If room doesn't exist, create it
        room = ChatRoom(
            id=webtoon_id,  # Use webtoon ID as room ID for simplicity
            webtoon_id=webtoon_id,
            name=f"Chat for Webtoon {str(webtoon_id)[:8]}",
        )
        
        # Save the room
        await self.storage.set(room_key, json.dumps(self._serialize_room(room)))
        
        return room


async def get_chat_repository(storage: StorageProvider) -> ChatRepository:
    """
    Get a configured ChatRepository instance
    
    Args:
        storage: The storage provider to use
        
    Returns:
        ChatRepository instance
    """
    return ChatRepositoryRedis(storage)
