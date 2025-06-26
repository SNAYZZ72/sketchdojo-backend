"""
Unit tests for cache_keys.py
"""
import pytest
from uuid import UUID, uuid4

from app.infrastructure.utils.cache_keys import (
    cache_key,
    cache_pattern,
    cache_hash_key,
    cache_hash_pattern,
    cache_keys
)

def test_cache_key():
    """Test generating a cache key."""
    key = "test_key"
    result = cache_key(key)
    assert result == f"cache:{key}"

def test_cache_key_with_uuid():
    """Test generating a cache key with a UUID."""
    key = uuid4()
    result = cache_key(str(key))
    assert result == f"cache:{key}"

def test_cache_pattern():
    """Test generating a cache pattern."""
    # Test with specific key
    result = cache_pattern("test_key")
    assert result == "cache:test_key*"
    
    # Test with wildcard
    result = cache_pattern()
    assert result == "cache*"

def test_cache_hash_key():
    """Test generating a cache hash key."""
    namespace = "test_namespace"
    key = "test_key"
    result = cache_hash_key(namespace, key)
    assert result == f"cache:hash:{namespace}:{key}"

def test_cache_hash_pattern():
    """Test generating a cache hash pattern."""
    # Test with specific namespace
    namespace = "test_namespace"
    result = cache_hash_pattern(namespace)
    assert result == "cache:hash:test_namespace:*"
    
    # Test with wildcard - KeyGenerator adds an extra wildcard at the end
    result = cache_hash_pattern()
    assert result == "cache:hash:*:*"

def test_cache_keys_namespace():
    """Test the cache_keys namespace."""
    # Test key generation
    result = cache_keys.key("test", "key")
    assert result == "cache:test:key"
    
    # Test pattern generation
    result = cache_keys.pattern("test", "*")
    assert result == "cache:test:*"
