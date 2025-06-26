"""
Key generation utilities for cache-related Redis keys.
"""
from typing import Union
from uuid import UUID

from .key_generator import KeyGenerator

def cache_key(key: str) -> str:
    """
    Generate a Redis key for a cache entry.
    
    Args:
        key: The cache key
        
    Returns:
        str: The Redis key
    """
    return KeyGenerator.generate_key("cache", key)

def cache_pattern(key: Union[str, None] = None) -> str:
    """
    Generate a Redis key pattern for cache entries.
    
    Args:
        key: Optional key pattern (defaults to '*' for all cache keys)
        
    Returns:
        str: The Redis key pattern
    """
    if key is None:
        return KeyGenerator.generate_pattern("cache")
    return KeyGenerator.generate_pattern("cache", key)

def cache_hash_key(namespace: str, key: str) -> str:
    """
    Generate a Redis key for a cache hash.
    
    Args:
        namespace: The hash namespace
        key: The hash key
        
    Returns:
        str: The Redis key for the hash
    """
    return KeyGenerator.generate_key("cache", "hash", namespace, key)

def cache_hash_pattern(namespace: str = "*") -> str:
    """
    Generate a Redis key pattern for cache hashes.
    
    Args:
        namespace: Optional namespace pattern (defaults to '*')
        
    Returns:
        str: The Redis key pattern for hashes
    """
    return KeyGenerator.generate_pattern("cache", "hash", namespace, "*")

# Create a namespace for cache keys
cache_keys = KeyGenerator.for_namespace("cache")
