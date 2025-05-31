# =============================================================================
# app/core/redis.py
# =============================================================================
"""
Redis configuration and management
"""
from app.infrastructure.cache import cache_service, close_cache, init_cache, redis_client

# Export for easy imports
__all__ = ["redis_client", "cache_service", "init_cache", "close_cache"]
