# app/infrastructure/cache/redis_cache.py
"""
Redis cache implementation
"""
import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching implementation"""

    def __init__(self, redis_client: redis.Redis, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        logger.info("Initialized Redis cache")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache"""
        try:
            serialized_value = (
                json.dumps(value) if not isinstance(value, str) else value
            )
            ttl = ttl or self.default_ttl

            await self.redis.setex(key, ttl, serialized_value)
            logger.debug(f"Cached value for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {str(e)}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            value = await self.redis.get(key)
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
        """Delete a value from cache"""
        try:
            result = await self.redis.delete(key)
            logger.debug(f"Deleted cache for key: {key}")
            return bool(result)

        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking existence for key {key}: {str(e)}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {str(e)}")
            return None

    async def set_hash(self, key: str, mapping: Dict[str, Any]) -> bool:
        """Set a hash (dictionary) in cache"""
        try:
            # Serialize values
            serialized_mapping = {
                k: json.dumps(v) if not isinstance(v, str) else v
                for k, v in mapping.items()
            }

            await self.redis.hset(key, mapping=serialized_mapping)
            logger.debug(f"Set hash for key: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting hash for key {key}: {str(e)}")
            return False

    async def get_hash(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a hash from cache"""
        try:
            hash_data = await self.redis.hgetall(key)
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
            logger.error(f"Error getting hash for key {key}: {str(e)}")
            return None

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching a pattern"""
        try:
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
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
