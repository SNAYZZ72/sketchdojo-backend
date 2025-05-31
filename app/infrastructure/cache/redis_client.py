# =============================================================================
# app/infrastructure/cache/redis_client.py
# =============================================================================
import json
import logging
import pickle
from datetime import timedelta
from typing import Any, List, Optional, Union

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper with advanced caching features."""

    def __init__(self, url: str = None):
        self.url = url or settings.redis_url
        self._client: Optional[redis.Redis] = None
        self.default_ttl = settings.redis_cache_ttl

    async def connect(self):
        """Connect to Redis."""
        if not self._client:
            self._client = redis.from_url(
                self.url,
                decode_responses=False,  # We'll handle encoding/decoding
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self._client.ping()
            logger.info("Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> redis.Redis:
        """Get Redis client, ensuring connection."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode("utf-8")
        else:
            # Use pickle for complex objects
            return pickle.dumps(value)

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from Redis."""
        try:
            # Try JSON first (for simple types)
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(value)

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            serialized = self._serialize(value)
            if ttl is None:
                ttl = self.default_ttl

            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())

            return await self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {str(e)}")
            return False

    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for key."""
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {str(e)}")
            return False

    async def get_many(self, keys: List[str]) -> List[Any]:
        """Get multiple values from cache."""
        try:
            values = await self.client.mget(keys)
            result = []
            for value in values:
                if value is None:
                    result.append(None)
                else:
                    result.append(self._deserialize(value))
            return result
        except Exception as e:
            logger.error(f"Redis MGET error: {str(e)}")
            return [None] * len(keys)

    async def set_many(self, mapping: dict, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple key-value pairs."""
        try:
            # Serialize all values
            serialized = {k: self._serialize(v) for k, v in mapping.items()}

            # Use pipeline for atomic operation
            async with self.client.pipeline() as pipe:
                await pipe.mset(serialized)

                if ttl is not None:
                    if isinstance(ttl, timedelta):
                        ttl = int(ttl.total_seconds())

                    for key in mapping.keys():
                        await pipe.expire(key, ttl)

                await pipe.execute()

            return True
        except Exception as e:
            logger.error(f"Redis MSET error: {str(e)}")
            return False

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from cache."""
        try:
            if not keys:
                return 0
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE MANY error: {str(e)}")
            return 0

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key.decode("utf-8") if isinstance(key, bytes) else key)

            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR PATTERN error: {str(e)}")
            return 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value."""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {str(e)}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value."""
        try:
            return await self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR error for key {key}: {str(e)}")
            return 0
