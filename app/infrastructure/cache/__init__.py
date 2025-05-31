# =============================================================================
# app/infrastructure/cache/__init__.py
# =============================================================================
"""
Cache Infrastructure Package

Provides Redis-based caching with high-level service abstractions.
"""

from .cache_service import CacheService
from .redis_client import RedisClient

__all__ = ["RedisClient", "CacheService"]


# Global cache instances
redis_client = RedisClient()
cache_service = CacheService(redis_client)


async def init_cache():
    """Initialize cache connections."""
    await redis_client.connect()


async def close_cache():
    """Close cache connections."""
    await redis_client.disconnect()
