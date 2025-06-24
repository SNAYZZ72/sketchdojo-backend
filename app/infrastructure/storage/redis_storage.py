# app/infrastructure/storage/redis_storage.py
"""
Redis storage implementation
"""
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis_async
import redis as redis_sync
from pydantic import BaseModel

from app.application.interfaces.storage_provider import StorageProvider
from app.config import get_settings

logger = logging.getLogger(__name__)


class RedisStorage(StorageProvider):
    """Redis storage implementation"""

    def __init__(self, redis_url: str = None):
        """Initialize Redis storage with optional explicit URL override"""
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.max_connections = settings.redis_max_connections
        
        logger.info(f"Initializing Redis storage with URL: {self.redis_url}")
        
        # Async client for async operations
        self.async_pool = redis_async.ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.max_connections,
            decode_responses=True  # Auto-decode responses to strings
        )
        self.redis_client = redis_async.Redis.from_pool(self.async_pool)
        
        # Sync client for sync operations
        self.sync_client = redis_sync.Redis.from_url(
            self.redis_url,
            decode_responses=True  # Auto-decode responses to strings
        )
        
        logger.info(f"Using Redis storage at {self.redis_url}")

    async def store(self, key: str, data: Any) -> bool:
        """Store data in Redis"""
        try:
            if isinstance(data, (dict, list)) or hasattr(data, 'model_dump'):
                # For Pydantic models, use model_dump()
                if hasattr(data, 'model_dump'):
                    data_to_store = json.dumps(data.model_dump(), default=self._json_serializer)
                else:
                    # For normal dictionaries or lists
                    data_to_store = json.dumps(data, default=self._json_serializer)
            else:
                data_to_store = str(data)
            
            await self.redis_client.set(key, data_to_store)
            logger.debug(f"Stored data to Redis with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing data for key {key}: {str(e)}")
            return False
            
    async def set(self, key: str, data: Any) -> bool:
        """Alias for store method (for compatibility with RedisProvider)"""
        return await self.store(key, data)

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis"""
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        except Exception as e:
            logger.error(f"Error retrieving data for key {key}: {str(e)}")
            return None
            
    async def get(self, key: str) -> Optional[Any]:
        """Alias for retrieve method (for compatibility with RedisProvider)"""
        return await self.retrieve(key)

    async def delete(self, key: str) -> bool:
        """Delete data from Redis"""
        try:
            result = await self.redis_client.delete(key)
            success = result > 0
            if success:
                logger.debug(f"Deleted data with key: {key}")
            return success
        except Exception as e:
            logger.error(f"Error deleting data for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking existence for key {key}: {str(e)}")
            return False

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern"""
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []
            
    async def store_json(self, key: str, data: Dict[str, Any]) -> bool:
        """Store JSON serializable data"""
        try:
            data_to_store = json.dumps(data, default=self._json_serializer)
            await self.redis_client.set(key, data_to_store)
            logger.debug(f"Stored JSON data to Redis with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing JSON data for key {key}: {str(e)}")
            return False
            
    async def retrieve_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data"""
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
                
            return json.loads(data)
        except json.JSONDecodeError:
            logger.error(f"Data for key {key} is not valid JSON")
            return None
        except Exception as e:
            logger.error(f"Error retrieving JSON data for key {key}: {str(e)}")
            return None

    # Sync methods for compatibility with file storage - using sync Redis client directly
    def store_sync(self, key: str, data: Any) -> bool:
        """Sync version of store for compatibility"""
        try:
            if isinstance(data, (dict, list)) or hasattr(data, 'model_dump'):
                # For Pydantic models, use model_dump()
                if hasattr(data, 'model_dump'):
                    data_to_store = json.dumps(data.model_dump(), default=self._json_serializer)
                else:
                    # For normal dictionaries or lists
                    data_to_store = json.dumps(data, default=self._json_serializer)
            else:
                data_to_store = str(data)
            
            self.sync_client.set(key, data_to_store)
            logger.debug(f"Sync: Stored data to Redis with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing data for key {key}: {str(e)}")
            return False
    
    def retrieve_sync(self, key: str) -> Optional[Any]:
        """Sync version of retrieve for compatibility"""
        try:
            data = self.sync_client.get(key)
            if data is None:
                return None
            
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        except Exception as e:
            logger.error(f"Error retrieving data for key {key}: {str(e)}")
            return None
    
    def exists_sync(self, key: str) -> bool:
        """Sync version of exists for compatibility"""
        try:
            return self.sync_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking existence for key {key}: {str(e)}")
            return False
    
    def delete_sync(self, key: str) -> bool:
        """Sync version of delete for compatibility"""
        try:
            result = self.sync_client.delete(key)
            success = result > 0
            if success:
                logger.debug(f"Sync: Deleted data with key: {key}")
            return success
        except Exception as e:
            logger.error(f"Error deleting data for key {key}: {str(e)}")
            return False
    
    def list_keys_sync(self, pattern: str = "*") -> List[str]:
        """Sync version of list_keys for compatibility"""
        try:
            keys = []
            for key in self.sync_client.scan_iter(match=pattern):
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    # Redis List Operations
    async def get_list(self, key: str) -> List[str]:
        """Get all items from a Redis list"""
        try:
            return await self.redis_client.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Error retrieving list for key {key}: {str(e)}")
            return []
    
    async def append_to_list(self, key: str, value: str) -> bool:
        """Append value to a Redis list"""
        try:
            await self.redis_client.rpush(key, value)
            logger.debug(f"Appended value to list with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error appending to list for key {key}: {str(e)}")
            return False
    
    async def remove_from_list(self, key: str, value: str) -> bool:
        """Remove value from a Redis list"""
        try:
            count = await self.redis_client.lrem(key, 0, value)
            success = count > 0
            if success:
                logger.debug(f"Removed value from list with key: {key}")
            return success
        except Exception as e:
            logger.error(f"Error removing from list for key {key}: {str(e)}")
            return False

    # Sync versions of list operations for compatibility
    def get_list_sync(self, key: str) -> List[str]:
        """Sync version of get_list"""
        try:
            return self.sync_client.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Error retrieving list for key {key}: {str(e)}")
            return []
    
    def append_to_list_sync(self, key: str, value: str) -> bool:
        """Sync version of append_to_list"""
        try:
            self.sync_client.rpush(key, value)
            logger.debug(f"Sync: Appended value to list with key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error appending to list for key {key}: {str(e)}")
            return False
    
    def remove_from_list_sync(self, key: str, value: str) -> bool:
        """Sync version of remove_from_list"""
        try:
            count = self.sync_client.lrem(key, 0, value)
            success = count > 0
            if success:
                logger.debug(f"Sync: Removed value from list with key: {key}")
            return success
        except Exception as e:
            logger.error(f"Error removing from list for key {key}: {str(e)}")
            return False
            
    def _json_serializer(self, obj):
        """Custom JSON serializer to handle UUID and other custom types"""
        if isinstance(obj, UUID):
            return str(obj)
        # Handle other custom types as needed
        return str(obj)
