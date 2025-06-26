# app/infrastructure/cache/redis_cache.py
"""
Redis cache implementation with consistent key generation.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis

from ..utils.cache_keys import cache_key, cache_hash_key, cache_pattern

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching implementation"""

    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        logger.info("Initialized Redis cache")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: The cache key (will be prefixed with 'cache:')
            value: The value to cache (will be JSON-serialized if not a string)
            ttl: Optional TTL in seconds (defaults to instance default)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cache_key_str = cache_key(key)
            serialized_value = (
                json.dumps(value) if not isinstance(value, str) else value
            )
            ttl = ttl or self.default_ttl

            await self.redis.setex(cache_key_str, ttl, serialized_value)
            logger.debug(f"Cached value for key: {cache_key_str}")
            return True

        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {str(e)}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: The cache key (will be prefixed with 'cache:')
            
        Returns:
            The cached value, or None if not found or on error
        """
        try:
            cache_key_str = cache_key(key)
            value = await self.redis.get(cache_key_str)
            if value is None:
                return None

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: The cache key to delete (will be prefixed with 'cache:')
            
        Returns:
            bool: True if the key was deleted, False otherwise
        """
        try:
            cache_key_str = cache_key(key)
            result = await self.redis.delete(cache_key_str)
            logger.debug(f"Deleted cache for key: {cache_key_str}")
            return bool(result)

        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key to check (will be prefixed with 'cache:')
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        try:
            cache_key_str = cache_key(key)
            return bool(await self.redis.exists(cache_key_str))
        except Exception as e:
            logger.error(f"Error checking existence for key {key}: {str(e)}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a numeric value in the cache.
        
        Args:
            key: The cache key to increment (will be prefixed with 'cache:')
            amount: The amount to increment by (default: 1)
            
        Returns:
            The new value, or None on error
        """
        try:
            cache_key_str = cache_key(key)
            return await self.redis.incrby(cache_key_str, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {str(e)}")
            return None

    async def set_hash(self, namespace: str, key: str, mapping: Dict[str, Any]) -> bool:
        """
        Set a hash (dictionary) in cache.
        
        Args:
            namespace: The namespace for the hash
            key: The hash key
            mapping: Dictionary of field-value pairs to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate a consistent key for the hash
            hash_key = cache_hash_key(namespace, key)
            
            # Serialize values
            serialized_mapping = {
                k: json.dumps(v) if not isinstance(v, str) else v
                for k, v in mapping.items()
            }

            await self.redis.hset(hash_key, mapping=serialized_mapping)
            logger.debug(f"Set hash for key: {hash_key}")
            return True

        except Exception as e:
            logger.error(f"Error setting hash for namespace '{namespace}', key '{key}': {str(e)}")
            return False

    async def get_hash(self, namespace: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a hash from cache.
        
        Args:
            namespace: The namespace of the hash
            key: The hash key
            
        Returns:
            Dictionary with the hash data, or None if not found or on error
        """
        try:
            hash_key = cache_hash_key(namespace, key)
            hash_data = await self.redis.hgetall(hash_key)
            if not hash_data:
                return None

            # Deserialize values
            result = {}
            for k, v in hash_data.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v

            return result

        except Exception as e:
            logger.error(f"Error getting hash for namespace '{namespace}', key '{key}': {str(e)}")
            return None

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """
        List cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match keys against (will be prefixed with 'cache:')
            
        Returns:
            List of matching keys
        """
        try:
            # Ensure pattern is scoped to cache keys
            if not pattern.startswith("cache:"):
                pattern = cache_pattern(pattern)
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match keys against (will be prefixed with 'cache:')
            
        Returns:
            int: Number of keys deleted
        """
        try:
            # Ensure pattern is scoped to cache keys
            if not pattern.startswith("cache:"):
                pattern = cache_pattern(pattern)
                
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern {pattern}: {str(e)}")
            return 0

    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
