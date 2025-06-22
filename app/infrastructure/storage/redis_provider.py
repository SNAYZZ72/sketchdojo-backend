"""
Redis storage implementation
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union

import redis
import redis.asyncio

from app.application.interfaces.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class RedisProvider(StorageProvider):
    """Redis storage implementation"""

    def __init__(self, redis_url: str):
        # Initialize both sync and async clients for different contexts
        self.async_client = redis.asyncio.from_url(redis_url, decode_responses=True)
        self.sync_client = redis.from_url(redis_url, decode_responses=True)
        self.redis_url = redis_url
        logger.info(f"Initialized Redis storage at: {redis_url} with both sync and async clients")

    async def store(self, key: str, data: Any) -> bool:
        """Store data in Redis asynchronously"""
        try:
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str)
            else:
                serialized_data = str(data)
                
            await self.async_client.set(key, serialized_data)
            logger.debug(f"Stored data for key: {key} asynchronously")
            return True
        except Exception as e:
            logger.error(f"Error storing data for key {key} asynchronously: {str(e)}")
            return False
    
    async def set(self, key: str, data: Any) -> bool:
        """Alias for store method"""
        return await self.store(key, data)
            
    def store_sync(self, key: str, data: Any) -> bool:
        """Store data in Redis synchronously (for use in Celery tasks)"""
        try:
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str)
            else:
                serialized_data = str(data)
                
            self.sync_client.set(key, serialized_data)
            logger.debug(f"Stored data for key: {key} synchronously")
            return True
        except Exception as e:
            logger.error(f"Error storing data for key {key} synchronously: {str(e)}")
            return False

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis asynchronously"""
        try:
            data = await self.async_client.get(key)
            
            if data is None:
                return None
                
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
                
        except Exception as e:
            logger.error(f"Error retrieving data for key {key} asynchronously: {str(e)}")
            return None
            
    async def get(self, key: str) -> Optional[Any]:
        """Alias for retrieve method"""
        return await self.retrieve(key)
            
    def retrieve_sync(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis synchronously (for use in Celery tasks)"""
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
            logger.error(f"Error retrieving data for key {key} synchronously: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete data from Redis"""
        try:
            deleted = await self.redis_client.delete(key)
            if deleted > 0:
                logger.debug(f"Deleted data for key: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting data for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking if key {key} exists: {str(e)}")
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
        """Store JSON data"""
        return await self.store(key, data)

    async def retrieve_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data"""
        try:
            data = await self.retrieve(key)
            if isinstance(data, dict):
                return data
            return None
        except Exception as e:
            logger.error(f"Error retrieving JSON for key {key}: {str(e)}")
            return None

    async def get_list(self, key: str) -> List[str]:
        """Get all items from a Redis list"""
        try:
            items = await self.async_client.lrange(key, 0, -1)
            logger.debug(f"Retrieved {len(items)} items from list: {key}")
            return items
        except Exception as e:
            logger.error(f"Error retrieving list for key {key}: {str(e)}")
            return []
    
    async def append_to_list(self, key: str, value: str) -> bool:
        """Append an item to the end of a Redis list (right push)"""
        try:
            await self.async_client.rpush(key, value)
            logger.debug(f"Appended item to list: {key}")
            return True
        except Exception as e:
            logger.error(f"Error appending to list for key {key}: {str(e)}")
            return False
    
    async def prepend_to_list(self, key: str, value: str) -> bool:
        """Prepend an item to the beginning of a Redis list (left push)"""
        try:
            await self.async_client.lpush(key, value)
            logger.debug(f"Prepended item to list: {key}")
            return True
        except Exception as e:
            logger.error(f"Error prepending to list for key {key}: {str(e)}")
            return False
            
    async def close(self):
        """Close Redis connection"""
        await self.async_client.close()
        await self.sync_client.close()
        logger.info("Closed Redis connections")
