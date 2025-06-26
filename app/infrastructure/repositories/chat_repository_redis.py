# app/infrastructure/repositories/chat_repository_redis.py
"""
Redis implementation of the ChatRepository using BaseRedisRepository
"""
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.chat import ChatMessage, ChatRoom
from app.domain.mappers.chat_mapper import ChatDataMapper
from app.domain.repositories.chat_repository import ChatRepository
from ..utils.key_generator import chat_keys
from .base_redis_repository import BaseRedisRepository

logger = logging.getLogger(__name__)


class ChatRepositoryRedis(BaseRedisRepository[ChatMessage], ChatRepository):
    """Redis implementation of the ChatRepository"""

    def __init__(self, storage: StorageProvider, mapper: ChatDataMapper = None):
        super().__init__(
            storage=storage,
            key_prefix=chat_keys.key("message"),
            ttl_seconds=86400 * 30  # 30 days TTL
        )
        self.mapper = mapper or ChatDataMapper()
        logger.info("ChatRepositoryRedis initialized")
        
    @property
    def entity_class(self) -> Type[ChatMessage]:
        return ChatMessage

    def _get_room_key(self, entity_id: Union[UUID, str, int]) -> str:
        """Get storage key for room entity ID"""
        return chat_keys.room(entity_id)
    
    def _get_webtoon_messages_key(self, webtoon_id: Union[UUID, str, int]) -> str:
        """Get storage key for webtoon messages list"""
        return chat_keys.webtoon_messages(webtoon_id)
        
    def _get_entity_key(self, entity_id: Union[UUID, str, int]) -> str:
        """
        Get the Redis key for an entity ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            str: The Redis key
        """
        return f"{self.key_prefix}:{str(entity_id)}"

    def _serialize_entity(self, entity: ChatMessage) -> str:
        """Serialize chat message to JSON string"""
        data = self.mapper.message_to_dict(entity)
        return json.dumps(data)
        
    def _deserialize_entity(self, data: str, entity_class: Type[ChatMessage] = None) -> ChatMessage:
        """Deserialize JSON string to ChatMessage"""
        data_dict = json.loads(data) if isinstance(data, str) else data
        return self.mapper.message_from_dict(data_dict)
    
    async def save(self, entity: ChatMessage) -> ChatMessage:
        """Save a chat message (create or update)"""
        try:
            # First save the message using base repository
            entity = await super().save(entity)
            
            # Add to webtoon messages list if webtoon_id is present
            if entity.webtoon_id:
                webtoon_messages_key = self._get_webtoon_messages_key(entity.webtoon_id)
                # Use a set to avoid duplicates
                await self.storage.add_to_sorted_set(
                    webtoon_messages_key,
                    {str(entity.id): datetime.now(UTC).timestamp()}
                )
                
            return entity
        except Exception as e:
            self.logger.error("Error saving chat message %s: %s", entity.id, str(e))
            raise
    
    async def save_message(self, entity: ChatMessage) -> ChatMessage:
        """Save a chat message (create or update) - for backward compatibility"""
        return await self.save(entity)
    
    async def create(self, entity: ChatMessage) -> ChatMessage:
        """Create a new chat message (delegates to save)"""
        return await self.save(entity)
        
    async def update(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[ChatMessage]:
        """Update an entity"""
        try:
            existing_entity = await self.get_by_id(entity_id)
            if not existing_entity:
                self.logger.warning("Entity %s not found for update", entity_id)
                return None
                
            # Update fields
            for key, value in data.items():
                if hasattr(existing_entity, key):
                    setattr(existing_entity, key, value)
            
            # Save updated entity
            return await self.save(existing_entity)
        except Exception as e:
            logger.error(f"Error updating chat message {entity_id}: {str(e)}")
            return None

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[ChatMessage]:
        """Get all chat messages with optional filtering"""
        try:
            # For this repository, we'll delegate to get_by_webtoon_id if webtoon_id is provided
            webtoon_id = filters.get("webtoon_id")
            if webtoon_id:
                return await self.get_by_webtoon_id(webtoon_id, limit, skip)
                
            # Get all message keys
            pattern = f"{self.message_key_prefix}*"
            message_keys = await self.storage.list_pattern(pattern)
            
            # Apply pagination
            paginated_keys = message_keys[skip:skip + limit]
            
            # Get messages by keys
            messages = []
            for key in paginated_keys:
                data = await self.storage.retrieve(key)
                if data:
                    messages.append(self.mapper.message_from_dict(data))
                    
            return messages
        except Exception as e:
            logger.error(f"Error getting all chat messages: {str(e)}")
            return []

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a chat message"""
        try:
            # Get the message first to know its webtoon_id
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
        except Exception as e:
            logger.error(f"Error deleting chat message {entity_id}: {str(e)}")
            return False
            
    async def exists(self, entity_id: UUID) -> bool:
        """Check if chat message exists"""
        try:
            message_key = self._get_message_key(entity_id)
            return await self.storage.exists(message_key)
        except Exception as e:
            logger.error(f"Error checking existence of chat message {entity_id}: {str(e)}")
            return False
            
    async def update_fields(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[ChatMessage]:
        """Update specific fields of a chat message"""
        try:
            # Get the existing message
            message = await self.get_by_id(entity_id)
            if not message:
                logger.warning(f"Cannot update fields for non-existent message: {entity_id}")
                return None
                
            # Get the current data
            message_key = self._get_message_key(entity_id)
            current_data = await self.storage.retrieve(message_key)
            if not current_data:
                return None
                
            if isinstance(current_data, str):
                current_data = json.loads(current_data)
            
            # Update fields
            current_data.update(data)
            
            # Save updated data using store for test compatibility
            await self.storage.store(message_key, json.dumps(current_data) if isinstance(current_data, dict) else current_data)
            
            # Return updated entity
            return self.mapper.message_from_dict(current_data)
        except Exception as e:
            logger.error(f"Error updating fields for chat message {entity_id}: {str(e)}")
            return None

    async def get_by_webtoon_id(self, webtoon_id: UUID, limit: int = 100, skip: int = 0) -> List[ChatMessage]:
        """Get chat messages for a specific webtoon
        
        This method retrieves messages for a webtoon using efficient batch fetching to minimize
        Redis round trips. Messages are returned in reverse chronological order (newest first).
        
        Args:
            webtoon_id: ID of the webtoon
            limit: Maximum number of messages to return (default: 100, max: 1000)
            skip: Number of messages to skip (for pagination)
            
        Returns:
            List of ChatMessage objects, ordered by timestamp (newest first)
            
        Raises:
            ValueError: If limit is invalid
        """
        # Validate input parameters
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")
            
        # Enforce maximum page size
        limit = min(limit, 1000)
        
        try:
            webtoon_messages_key = self._get_webtoon_messages_key(webtoon_id)
            
            # Get message IDs with scores (timestamps) in reverse order (newest first)
            message_ids = await self.storage.get_sorted_set_range(
                webtoon_messages_key,
                start=skip,
                stop=skip + limit - 1,
                desc=True,
                with_scores=False
            )
            
            if not message_ids:
                return []
                
            # Batch fetch all messages in a single Redis operation
            messages = await self._batch_get_messages(message_ids)
            
            # Ensure we maintain the original sort order from the sorted set
            message_map = {str(msg.id): msg for msg in messages}
            return [message_map[msg_id] for msg_id in message_ids if msg_id in message_map]
            
        except Exception as e:
            logger.error("Error getting chat messages for webtoon %s: %s", webtoon_id, str(e))
            return []
    
    async def _batch_get_messages(self, message_ids: List[Union[UUID, str]]) -> List[ChatMessage]:
        """
        Batch fetch multiple messages by their IDs.
        
        Args:
            message_ids: List of message IDs to fetch
            
        Returns:
            List of ChatMessage objects
        """
        if not message_ids:
            return []
            
        try:
            # Use pipeline to fetch multiple messages in a single round trip
            pipeline = self.storage.redis_client.pipeline()
            
            # Queue up all the get operations
            for msg_id in message_ids:
                msg_key = self._get_entity_key(msg_id)
                pipeline.get(msg_key)
                
            # Execute all operations in a single round trip
            results = await pipeline.execute()
            
            # Process results
            messages = []
            for data in results:
                if data:
                    try:
                        message = self._deserialize_entity(data)
                        messages.append(message)
                    except Exception as e:
                        self.logger.error("Error deserializing message: %s", str(e))
                        continue
                        
            return messages
            
        except Exception as e:
            self.logger.error("Error in batch message fetch: %s", str(e))
            return []

    async def get_messages_by_webtoon(
        self, webtoon_id: Union[UUID, str, int], skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get messages for a specific webtoon with pagination.
        
        Args:
            webtoon_id: ID of the webtoon
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            
        Returns:
            List of ChatMessage objects, ordered by timestamp (newest first)
        """
        try:
            webtoon_messages_key = self._get_webtoon_messages_key(webtoon_id)
            
            # Get message IDs with scores (timestamps) in reverse order (newest first)
            message_ids = await self.storage.get_sorted_set_range(
                webtoon_messages_key,
                start=skip,
                stop=skip + limit - 1,
                desc=True,
                with_scores=False
            )
            
            if not message_ids:
                return []
                
            # Batch fetch all messages in a single Redis operation
            messages = await self._batch_get_messages(message_ids)
            
            # Ensure we maintain the original sort order from the sorted set
            message_map = {str(msg.id): msg for msg in messages}
            return [message_map[msg_id] for msg_id in message_ids if msg_id in message_map]
            
        except Exception as e:
            self.logger.error("Error getting messages for webtoon %s: %s", webtoon_id, str(e))
            return []

    async def save_room(self, room: ChatRoom) -> ChatRoom:
        """Save a chat room"""
        try:
            # Serialize the room
            data = self.mapper.room_to_dict(room)
            
            # Save room data
            room_key = self._get_room_key(room.id)
            success = await self.storage.set(room_key, json.dumps(data))
            
            if not success:
                raise RuntimeError(f"Failed to save chat room {room.id}")
                
            return room
        except Exception as e:
            logger.error(f"Error saving chat room {room.id}: {str(e)}")
            raise
            
    async def get_room(self, room_id: UUID) -> Optional[ChatRoom]:
        """Get room by ID"""
        try:
            room_key = self._get_room_key(room_id)
            data = await self.storage.get(room_key)
            
            if not data:
                return None
                
            return self.mapper.room_from_dict(data)
        except Exception as e:
            logger.error(f"Failed to get chat room {room_id}: {str(e)}")
            return None
            
    async def get_chat_history(self, webtoon_id: UUID, limit: int = 100) -> List[ChatMessage]:
        """Get chat history for a webtoon
        
        This is a convenience method that delegates to get_by_webtoon_id with a default
        skip value of 0. It maintains backward compatibility while using the optimized
        batch fetching implementation.
        
        Args:
            webtoon_id: ID of the webtoon
            limit: Maximum number of messages to return (default: 100, max: 1000)
            
        Returns:
            List of ChatMessage objects, ordered by timestamp (newest first)
            
        Raises:
            ValueError: If limit is invalid
        """
        return await self.get_by_webtoon_id(webtoon_id, limit=limit, skip=0)
            
    async def get_rooms_for_webtoon(self, webtoon_id: UUID) -> List[ChatRoom]:
        """Get all rooms for a specific webtoon"""
        try:
            # Pattern to match rooms for this webtoon
            room_pattern = f"{self.room_key_prefix}{webtoon_id}"
            room_keys = await self.storage.list_pattern(room_pattern)
            
            rooms = []
            for room_key in room_keys:
                # Extract room ID from key
                room_id_str = room_key.replace(self.room_key_prefix, "")
                room = await self.get_room(UUID(room_id_str))
                if room:
                    rooms.append(room)
            
            return rooms
        except Exception as e:
            logger.error(f"Error getting rooms for webtoon {webtoon_id}: {str(e)}")
            return []
            
    async def delete_room(self, room_id: UUID) -> bool:
        """Delete a chat room"""
        try:
            room_key = self._get_room_key(room_id)
            success = await self.storage.delete(room_key)
            return success
        except Exception as e:
            logger.error(f"Error deleting chat room {room_id}: {str(e)}")
            return False
            
    async def room_exists(self, room_id: UUID) -> bool:
        """Check if room exists"""
        try:
            room_key = self._get_room_key(room_id)
            return await self.storage.exists(room_key)
        except Exception as e:
            logger.error(f"Error checking existence of chat room {room_id}: {str(e)}")
            return False
            
    async def get_chat_room_by_webtoon_id(self, webtoon_id: UUID) -> Optional[ChatRoom]:
        """Get chat room for a specific webtoon"""
        try:
            # For this implementation, we'll use a consistent room ID based on the webtoon ID
            room = await self.get_room(webtoon_id)
            
            if room:
                return room
                    
            # If room doesn't exist, create it
            room = ChatRoom(
                id=webtoon_id,  # Use webtoon ID as room ID for simplicity
                webtoon_id=webtoon_id,
                name=f"Chat for Webtoon {str(webtoon_id)[:8]}",
            )
            
            # Save the room
            await self.save_room(room)
            
            return room
        except Exception as e:
            logger.error(f"Error getting chat room for webtoon {webtoon_id}: {str(e)}")
            return None

    async def save_chat_room(self, room: ChatRoom) -> ChatRoom:
        """Save a chat room"""
        try:
            room_key = self._get_room_key(room.id)
            result = await self.storage.set(room_key, json.dumps(self.mapper.room_to_dict(room)))
            if not result:
                raise RuntimeError(f"Failed to save chat room {room.id}")
            return room
        except Exception as e:
            logger.error(f"Error saving chat room {room.id}: {str(e)}")
            raise  # Removed the duplicate raise statement

# Factory function removed as dependency injection is now handled in app/dependencies.py
