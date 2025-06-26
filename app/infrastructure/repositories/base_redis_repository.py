"""
Base Redis repository implementation with common CRUD operations.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from app.domain.repositories.base_repository import BaseRepository
from app.application.interfaces.storage_provider import StorageProvider

T = TypeVar('T')

class BaseRedisRepository(BaseRepository[T], ABC):
    """
    Base Redis repository implementation with common CRUD operations.
    """
    
    def __init__(
        self,
        storage: StorageProvider,
        key_prefix: str,
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize the base Redis repository.
        
        Args:
            storage: The storage provider instance
            key_prefix: Prefix for all keys used by this repository
            ttl_seconds: Optional TTL in seconds for stored values
        """
        self.storage = storage
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def _get_entity_key(self, entity_id: Union[UUID, str, int]) -> str:
        """
        Get the Redis key for an entity ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            str: The Redis key
        """
        return f"{self.key_prefix}:{str(entity_id)}"
    
    @abstractmethod
    def _serialize_entity(self, entity: T) -> str:
        """
        Serialize an entity to a string for storage.
        
        Args:
            entity: The entity to serialize
            
        Returns:
            str: Serialized entity
        """
        return json.dumps(entity.dict() if hasattr(entity, 'dict') else vars(entity))
    
    @abstractmethod
    def _deserialize_entity(self, data: str, entity_class: Type[T]) -> T:
        """
        Deserialize data from storage to an entity.
        
        Args:
            data: Serialized data
            entity_class: The entity class to instantiate
            
        Returns:
            T: Deserialized entity
        """
        data_dict = json.loads(data) if isinstance(data, str) else data
        if hasattr(entity_class, 'parse_obj'):  # Pydantic model
            return entity_class.parse_obj(data_dict)
        return entity_class(**data_dict)
    
    async def save(self, entity: T) -> T:
        """
        Save an entity (create or update).
        
        Args:
            entity: The entity to save
            
        Returns:
            T: The saved entity
        """
        try:
            entity_id = str(getattr(entity, 'id'))
            key = self._get_entity_key(entity_id)
            serialized = self._serialize_entity(entity)
            
            success = await self.storage.set(key, serialized)
            if not success:
                raise RuntimeError(f"Failed to save entity {entity_id}")
                
            if self.ttl_seconds:
                await self.storage.expire(key, self.ttl_seconds)
                
            self.logger.debug("Saved entity %s", entity_id)
            return entity
            
        except Exception as e:
            self.logger.error("Error saving entity: %s", str(e), exc_info=True)
            raise
    
    async def get_by_id(self, entity_id: Union[UUID, str, int]) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            Optional[T]: The entity if found, None otherwise
        """
        try:
            key = self._get_entity_key(entity_id)
            data = await self.storage.get(key)
            
            if not data:
                return None
                
            return self._deserialize_entity(data, self.entity_class)
            
        except Exception as e:
            self.logger.error("Error getting entity %s: %s", entity_id, str(e))
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """
        Get all entities with optional pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Filter criteria
            
        Returns:
            List[T]: List of entities
        """
        # Default implementation - should be overridden by subclasses
        # with more efficient implementations
        all_entities = []
        cursor = 0
        pattern = f"{self.key_prefix}:*"
        
        while True:
            cursor, keys = await self.storage.scan(cursor, pattern, count=100)
            
            for key in keys:
                data = await self.storage.get(key)
                if data:
                    entity = self._deserialize_entity(data, self.entity_class)
                    if self._matches_filters(entity, filters):
                        all_entities.append(entity)
            
            if cursor == 0:
                break
        
        return all_entities[skip:skip + limit] if limit else all_entities[skip:]
    
    async def update_fields(self, entity_id: Union[UUID, str, int], data: Dict[str, Any]) -> Optional[T]:
        """
        Update specific fields of an entity.
        
        Args:
            entity_id: The ID of the entity to update
            data: Dictionary of fields to update
            
        Returns:
            Optional[T]: The updated entity if found, None otherwise
        """
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                return None
                
            # Update entity fields
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                    
            # Save the updated entity
            return await self.save(entity)
            
        except Exception as e:
            self.logger.error("Error updating entity %s: %s", entity_id, str(e))
            raise
    
    async def delete(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            key = self._get_entity_key(entity_id)
            return await self.storage.delete(key)
        except Exception as e:
            self.logger.error("Error deleting entity %s: %s", entity_id, str(e))
            return False
    
    async def exists(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Check if an entity exists.
        
        Args:
            entity_id: The ID of the entity to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            key = self._get_entity_key(entity_id)
            return await self.storage.exists(key)
        except Exception as e:
            self.logger.error("Error checking if entity %s exists: %s", entity_id, str(e))
            return False
    
    def _matches_filters(self, entity: T, filters: Dict[str, Any]) -> bool:
        """
        Check if an entity matches all the given filters.
        
        Args:
            entity: The entity to check
            filters: Dictionary of field names and expected values
            
        Returns:
            bool: True if all filters match, False otherwise
        """
        for field, value in filters.items():
            if not hasattr(entity, field) or getattr(entity, field) != value:
                return False
        return True
    
    @property
    @abstractmethod
    def entity_class(self) -> Type[T]:
        """
        Get the entity class for this repository.
        
        Returns:
            Type[T]: The entity class
        """
        raise NotImplementedError("Subclasses must implement entity_class property")
