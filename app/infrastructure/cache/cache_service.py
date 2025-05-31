# =============================================================================
# app/infrastructure/cache/cache_service.py
# =============================================================================
import asyncio
import hashlib
import json
import logging
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, List, Optional, Union

from .redis_client import RedisClient

logger = logging.getLogger(__name__)


class CacheService:
    """High-level caching service with decorators and utilities."""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.key_prefix = "sketchdojo:"

    def _make_key(self, *parts: str) -> str:
        """Create cache key from parts."""
        return self.key_prefix + ":".join(str(part) for part in parts)

    def _hash_args(self, *args, **kwargs) -> str:
        """Create hash from function arguments."""
        # Create deterministic string from args and kwargs
        arg_str = json.dumps(
            {"args": args, "kwargs": sorted(kwargs.items())}, sort_keys=True, default=str
        )

        return hashlib.md5(arg_str.encode()).hexdigest()

    async def get_user_cache(self, user_id: str, cache_type: str, key: str) -> Any:
        """Get user-specific cached value."""
        cache_key = self._make_key("user", user_id, cache_type, key)
        return await self.redis.get(cache_key)

    async def set_user_cache(
        self,
        user_id: str,
        cache_type: str,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """Set user-specific cached value."""
        cache_key = self._make_key("user", user_id, cache_type, key)
        return await self.redis.set(cache_key, value, ttl)

    async def clear_user_cache(self, user_id: str, cache_type: str = None) -> int:
        """Clear user cache, optionally for specific type."""
        if cache_type:
            pattern = self._make_key("user", user_id, cache_type, "*")
        else:
            pattern = self._make_key("user", user_id, "*")

        return await self.redis.clear_pattern(pattern)

    async def get_project_cache(self, project_id: str, key: str) -> Any:
        """Get project-specific cached value."""
        cache_key = self._make_key("project", project_id, key)
        return await self.redis.get(cache_key)

    async def set_project_cache(
        self, project_id: str, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set project-specific cached value."""
        cache_key = self._make_key("project", project_id, key)
        return await self.redis.set(cache_key, value, ttl)

    async def clear_project_cache(self, project_id: str) -> int:
        """Clear all cache for a project."""
        pattern = self._make_key("project", project_id, "*")
        return await self.redis.clear_pattern(pattern)

    async def get_task_cache(self, task_id: str, key: str) -> Any:
        """Get task-specific cached value."""
        cache_key = self._make_key("task", task_id, key)
        return await self.redis.get(cache_key)

    async def set_task_cache(
        self, task_id: str, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set task-specific cached value."""
        cache_key = self._make_key("task", task_id, key)
        return await self.redis.set(cache_key, value, ttl)

    def cached(
        self, ttl: Union[int, timedelta] = 3600, key_template: str = None, namespace: str = "func"
    ):
        """Decorator to cache function results."""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_template:
                    # Use template with function args
                    try:
                        cache_key = self._make_key(
                            namespace, func.__name__, key_template.format(*args, **kwargs)
                        )
                    except (IndexError, KeyError):
                        cache_key = self._make_key(
                            namespace, func.__name__, self._hash_args(*args, **kwargs)
                        )
                else:
                    cache_key = self._make_key(
                        namespace, func.__name__, self._hash_args(*args, **kwargs)
                    )

                # Try to get from cache
                cached_result = await self.redis.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT for {func.__name__}")
                    return cached_result

                # Execute function and cache result
                logger.debug(f"Cache MISS for {func.__name__}")
                result = await func(*args, **kwargs)

                # Cache the result
                await self.redis.set(cache_key, result, ttl)

                return result

            return wrapper

        return decorator

    def cache_invalidate(self, pattern: str = None, namespace: str = "func"):
        """Decorator to invalidate cache after function execution."""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Execute function first
                result = await func(*args, **kwargs)

                # Invalidate cache
                if pattern:
                    try:
                        invalidate_pattern = self._make_key(
                            namespace, pattern.format(*args, **kwargs)
                        )
                    except (IndexError, KeyError):
                        invalidate_pattern = self._make_key(namespace, "*")
                else:
                    invalidate_pattern = self._make_key(namespace, func.__name__, "*")

                await self.redis.clear_pattern(invalidate_pattern)
                logger.debug(f"Cache invalidated for pattern: {invalidate_pattern}")

                return result

            return wrapper

        return decorator

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[Union[int, timedelta]] = None,
        *args,
        **kwargs,
    ) -> Any:
        """Get value from cache or execute factory function and cache result."""
        cached_value = await self.redis.get(key)
        if cached_value is not None:
            return cached_value

        # Execute factory function
        if asyncio.iscoroutinefunction(factory):
            value = await factory(*args, **kwargs)
        else:
            value = factory(*args, **kwargs)

        # Cache the result
        await self.redis.set(key, value, ttl)

        return value

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            info = await self.redis.client.info()
            return {
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                )
                * 100,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
