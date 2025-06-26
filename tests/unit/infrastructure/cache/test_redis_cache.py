"""
Unit tests for RedisCache with consistent key generation.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.utils.cache_keys import cache_key, cache_hash_key

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return AsyncMock()

@pytest.fixture
def cache(mock_redis):
    """Create a RedisCache instance with a mock Redis client."""
    return RedisCache(redis_client=mock_redis, default_ttl=3600)

@pytest.mark.asyncio
async def test_set(cache, mock_redis):
    """Test setting a value in the cache."""
    test_key = "test_key"
    test_value = {"test": "value"}
    
    result = await cache.set(test_key, test_value)
    
    # Check that the key was properly prefixed
    expected_key = cache_key(test_key)
    mock_redis.setex.assert_awaited_once()
    args, kwargs = mock_redis.setex.call_args
    assert args[0] == expected_key
    assert json.loads(args[2]) == test_value
    assert result is True

@pytest.mark.asyncio
async def test_get(cache, mock_redis):
    """Test getting a value from the cache."""
    test_key = "test_key"
    test_value = {"test": "value"}
    
    # Mock the Redis get response
    mock_redis.get.return_value = json.dumps(test_value)
    
    result = await cache.get(test_key)
    
    # Check that the key was properly prefixed
    expected_key = cache_key(test_key)
    mock_redis.get.assert_awaited_once_with(expected_key)
    assert result == test_value

@pytest.mark.asyncio
async def test_delete(cache, mock_redis):
    """Test deleting a value from the cache."""
    test_key = "test_key"
    mock_redis.delete.return_value = 1  # Indicates success
    
    result = await cache.delete(test_key)
    
    expected_key = cache_key(test_key)
    mock_redis.delete.assert_awaited_once_with(expected_key)
    assert result is True

@pytest.mark.asyncio
async def test_exists(cache, mock_redis):
    """Test checking if a key exists in the cache."""
    test_key = "test_key"
    mock_redis.exists.return_value = 1  # Key exists
    
    result = await cache.exists(test_key)
    
    expected_key = cache_key(test_key)
    mock_redis.exists.assert_awaited_once_with(expected_key)
    assert result is True

@pytest.mark.asyncio
async def test_increment(cache, mock_redis):
    """Test incrementing a numeric value in the cache."""
    test_key = "counter"
    mock_redis.incrby.return_value = 2
    
    result = await cache.increment(test_key, 1)
    
    expected_key = cache_key(test_key)
    mock_redis.incrby.assert_awaited_once_with(expected_key, 1)
    assert result == 2

@pytest.mark.asyncio
async def test_set_hash(cache, mock_redis):
    """Test setting a hash in the cache."""
    namespace = "test_namespace"
    key = "test_hash"
    mapping = {"field1": "value1", "field2": 42}
    
    result = await cache.set_hash(namespace, key, mapping)
    
    expected_key = cache_hash_key(namespace, key)
    mock_redis.hset.assert_awaited_once()
    args, kwargs = mock_redis.hset.call_args
    assert args[0] == expected_key
    assert "mapping" in kwargs
    assert json.loads(kwargs["mapping"]["field2"]) == 42
    assert result is True

@pytest.mark.asyncio
async def test_get_hash(cache, mock_redis):
    """Test getting a hash from the cache."""
    namespace = "test_namespace"
    key = "test_hash"
    hash_data = {"field1": json.dumps("value1"), "field2": json.dumps(42)}
    
    mock_redis.hgetall.return_value = hash_data
    
    result = await cache.get_hash(namespace, key)
    
    expected_key = cache_hash_key(namespace, key)
    mock_redis.hgetall.assert_awaited_once_with(expected_key)
    assert result == {"field1": "value1", "field2": 42}

@pytest.mark.asyncio
async def test_list_keys(cache, mock_redis):
    """Test listing keys with a pattern."""
    pattern = "test_*"
    mock_redis.keys.return_value = [b"cache:test_1", b"cache:test_2"]
    
    result = await cache.list_keys(pattern)
    
    # Should have added cache: prefix and additional wildcard to the pattern
    mock_redis.keys.assert_awaited_once_with("cache:test_**")
    assert result == [b"cache:test_1", b"cache:test_2"]

@pytest.mark.asyncio
async def test_clear_pattern(cache, mock_redis):
    """Test clearing keys matching a pattern."""
    pattern = "test_*"
    mock_redis.keys.return_value = [b"cache:test_1", b"cache:test_2"]
    mock_redis.delete.return_value = 2
    
    result = await cache.clear_pattern(pattern)
    
    # Should have added cache: prefix and additional wildcard to the pattern
    mock_redis.keys.assert_awaited_once_with("cache:test_**")
    mock_redis.delete.assert_awaited_once_with(b"cache:test_1", b"cache:test_2")
    assert result == 2

@pytest.mark.asyncio
async def test_health_check_healthy(cache, mock_redis):
    """Test health check when Redis is healthy."""
    mock_redis.ping.return_value = True
    
    result = await cache.health_check()
    
    mock_redis.ping.assert_awaited_once()
    assert result is True

@pytest.mark.asyncio
async def test_health_check_unhealthy(cache, mock_redis):
    """Test health check when Redis is not healthy."""
    mock_redis.ping.side_effect = Exception("Connection error")
    
    result = await cache.health_check()
    
    assert result is False
