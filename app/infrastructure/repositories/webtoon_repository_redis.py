"""
Redis implementation of the WebtoonRepository interface.
"""
import json
import logging
from typing import Any, Dict, Optional, Type, Union
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.webtoon import Webtoon
from app.domain.mappers.webtoon_mapper import WebtoonDataMapper
from app.domain.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.base_redis_repository import BaseRedisRepository
from app.infrastructure.utils.webtoon_keys import (
    webtoon_key,
    webtoon_list_key,
    webtoon_user_webtoons_key,
)

logger = logging.getLogger(__name__)

class WebtoonRepositoryRedis(BaseRedisRepository[Webtoon]):
    """
    Redis implementation of the WebtoonRepository interface.
    Uses BaseRedisRepository for common Redis operations.
    """
    
    @property
    def entity_class(self) -> type[Webtoon]:
        """Get the entity class this repository manages."""
        return Webtoon
    
    def __init__(
        self,
        storage: StorageProvider,
        ttl_seconds: int = 7 * 24 * 60 * 60,  # 7 days default TTL
        mapper: Optional[WebtoonDataMapper] = None,
    ):
        """
        Initialize the WebtoonRepositoryRedis.
        
        Args:
            storage: The storage provider instance
            ttl_seconds: TTL in seconds for stored webtoons
            mapper: Optional WebtoonDataMapper instance
        """
        super().__init__(
            storage=storage,
            key_prefix="webtoon",
            ttl_seconds=ttl_seconds
        )
        self.mapper = mapper or WebtoonDataMapper()
    
    def _get_entity_key(self, entity_id: Union[UUID, str]) -> str:
        """
        Get the Redis key for a webtoon ID.
        
        Args:
            entity_id: The webtoon ID
            
        Returns:
            str: The Redis key
        """
        return webtoon_key(entity_id)
    
    def _serialize_entity(self, entity: Webtoon) -> str:
        """
        Serialize a Webtoon entity to a JSON string.
        
        Args:
            entity: The Webtoon entity to serialize
            
        Returns:
            str: JSON string representation of the webtoon
        """
        try:
            webtoon_dict = self.mapper.to_dict(entity)
            return json.dumps(webtoon_dict, default=str)
        except Exception as e:
            self.logger.error(f"Error serializing webtoon {entity.id}: {str(e)}")
            raise
    
    def _deserialize_entity(self, data: Union[str, bytes, dict], entity_class: Type[Webtoon] = None) -> Webtoon:
        """
        Deserialize JSON data to a Webtoon entity.
        
        Args:
            data: JSON string, bytes, or dict containing webtoon data
            entity_class: The entity class to deserialize to (ignored, for compatibility with base class)
            
        Returns:
            Webtoon: The deserialized Webtoon entity
            
        Raises:
            ValueError: If data cannot be deserialized
        """
        try:
            if isinstance(data, (str, bytes)):
                data_dict = json.loads(data)
            elif isinstance(data, dict):
                data_dict = data
            else:
                raise ValueError("Data must be a JSON string, bytes, or dict")
                
            webtoon = self.mapper.from_dict(data_dict)
            if not webtoon:
                raise ValueError("Failed to deserialize webtoon")
                
            return webtoon
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
            raise ValueError("Invalid JSON data") from e
        except Exception as e:
            self.logger.error(f"Error deserializing webtoon: {str(e)}")
            raise
    
    async def save(self, entity: Webtoon) -> Webtoon:
        """
        Save a webtoon entity (create or update).
        
        Args:
            entity: The webtoon to save
            
        Returns:
            Webtoon: The saved webtoon
            
        Raises:
            RuntimeError: If the webtoon cannot be saved
        """
        try:
            # Save the webtoon using the parent class implementation
            saved_webtoon = await super().save(entity)
            
            # Add to the global webtoons set
            await self.storage.sadd(webtoon_list_key(), str(entity.id))
            
            # If the webtoon has a creator_id in metadata, add to user's webtoons
            creator_id = entity.metadata.get('creator_id')
            if creator_id:
                user_webtoons_key = webtoon_user_webtoons_key(creator_id)
                await self.storage.sadd(user_webtoons_key, str(entity.id))
            
            return saved_webtoon
            
        except Exception as e:
            self.logger.error(f"Error saving webtoon {entity.id}: {str(e)}")
            raise RuntimeError(f"Failed to save webtoon: {str(e)}")
    
    async def get_by_creator(self, user_id: Union[UUID, str]) -> list[Webtoon]:
        """
        Get all webtoons created by a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            list[Webtoon]: List of webtoons created by the user
        """
        try:
            user_webtoons_key = webtoon_user_webtoons_key(user_id)
            webtoon_ids = await self.storage.smembers(user_webtoons_key)
            
            if not webtoon_ids:
                return []
                
            # Get all webtoons
            webtoons = []
            for webtoon_id in webtoon_ids:
                webtoon_data = await self.storage.get(webtoon_key(webtoon_id))
                if webtoon_data:
                    try:
                        webtoon = self._deserialize_entity(webtoon_data)
                        webtoons.append(webtoon)
                    except Exception as e:
                        self.logger.error(f"Error deserializing webtoon {webtoon_id}: {str(e)}")
            
            return webtoons
            
        except Exception as e:
            self.logger.error(f"Error getting webtoons for user {user_id}: {str(e)}")
            return []
    
    async def delete(self, entity_id: Union[UUID, str]) -> bool:
        """
        Delete a webtoon by ID.
        
        Args:
            entity_id: The ID of the webtoon to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # First, get the webtoon to get the creator ID
            webtoon = await self.get_by_id(entity_id)
            if not webtoon:
                return False
                
            # Delete the webtoon
            deleted = await self.storage.delete(self._get_entity_key(entity_id))
            
            # Remove from the global set
            await self.storage.srem(webtoon_list_key(), str(entity_id))
            
            # Remove from the creator's set if creator_id exists in metadata
            creator_id = webtoon.metadata.get('creator_id')
            if creator_id:
                await self.storage.srem(webtoon_user_webtoons_key(creator_id), str(entity_id))
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Error deleting webtoon {entity_id}: {str(e)}")
            return False
    
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> list[Webtoon]:
        """
        Get all webtoons with optional pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Filter criteria
            
        Returns:
            list[Webtoon]: List of webtoons
        """
        try:
            # Get all webtoon IDs from the set
            all_webtoon_ids = await self.storage.smembers(webtoon_list_key())
            
            if not all_webtoon_ids:
                return []
                
            # Apply pagination
            webtoon_ids = list(all_webtoon_ids)[skip:skip + limit] if limit else list(all_webtoon_ids)[skip:]
            
            # Get all webtoons
            webtoons = []
            for webtoon_id in webtoon_ids:
                webtoon_data = await self.storage.get(webtoon_key(webtoon_id))
                if webtoon_data:
                    try:
                        webtoon = self._deserialize_entity(webtoon_data)
                        
                        # Apply filters if any
                        if self._matches_filters(webtoon, filters):
                            webtoons.append(webtoon)
                    except Exception as e:
                        self.logger.error(f"Error deserializing webtoon {webtoon_id}: {str(e)}")
            
            return webtoons
            
        except Exception as e:
            self.logger.error(f"Error getting all webtoons: {str(e)}")
            return []
    
    def _matches_filters(self, webtoon: Webtoon, filters: dict) -> bool:
        """
        Check if a webtoon matches all the given filters.
        
        Args:
            webtoon: The webtoon to check
            filters: Dictionary of filters
            
        Returns:
            bool: True if the webtoon matches all filters
        """
        for key, value in filters.items():
            # Handle special cases
            if key == 'is_published' and hasattr(webtoon, 'is_published'):
                if webtoon.is_published != value:
                    return False
            # Handle metadata filters
            elif key.startswith('metadata.') and hasattr(webtoon, 'metadata'):
                meta_key = key[9:]  # Remove 'metadata.' prefix
                if webtoon.metadata.get(meta_key) != value:
                    return False
            # Handle direct attributes
            elif hasattr(webtoon, key) and getattr(webtoon, key) != value:
                return False
                
        return True
    
    async def update_fields(
        self,
        entity_id: Union[UUID, str],
        data: Dict[str, Any],
    ) -> Optional[Webtoon]:
        """
        Update specific fields of a webtoon.
        
        Args:
            entity_id: The ID of the webtoon to update
            data: Dictionary of fields to update
            
        Returns:
            Optional[Webtoon]: The updated webtoon if successful, None otherwise
        """
        try:
            # Get the existing webtoon
            webtoon = await self.get_by_id(entity_id)
            if not webtoon:
                return None
                
            # Update the fields
            webtoon_dict = self.mapper.to_dict(webtoon)
            for key, value in data.items():
                if key in webtoon_dict:
                    webtoon_dict[key] = value
                elif key.startswith('metadata.') and 'metadata' in webtoon_dict:
                    meta_key = key[9:]  # Remove 'metadata.' prefix
                    webtoon_dict['metadata'][meta_key] = value
            
            # Convert back to entity
            updated_webtoon = self.mapper.from_dict(webtoon_dict)
            if not updated_webtoon:
                raise ValueError("Failed to update webtoon")
            
            # Save the updated webtoon
            return await self.save(updated_webtoon)
            
        except Exception as e:
            self.logger.error(f"Error updating webtoon {entity_id}: {str(e)}")
            return None
