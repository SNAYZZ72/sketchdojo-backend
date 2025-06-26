"""
Tests for RedisStorage implementation
"""
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY
import pytest
import pytest_asyncio
from typing import List, Tuple, Union, Any, AsyncGenerator, Dict

from app.infrastructure.storage.redis_storage import RedisStorage


class TestRedisStorage:
    """Test RedisStorage implementation"""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client with async methods"""
        mock_client = AsyncMock()
        
        # Configure the client to return test data
        async def mock_zrange(*args, **kwargs):
            if kwargs.get('withscores', False):
                return [
                    (b"item1", 1.0),
                    (b"item2", 2.0),
                    (b"item3", 3.0)
                ]
            return [b"item1", b"item2", b"item3"]
            
        async def mock_zrevrange(*args, **kwargs):
            if kwargs.get('withscores', False):
                return [
                    (b"item3", 3.0),
                    (b"item2", 2.0),
                    (b"item1", 1.0)
                ]
            return [b"item3", b"item2", b"item1"]
            
        # Create proper async mocks that track calls
        mock_client.zrange = AsyncMock(side_effect=mock_zrange)
        mock_client.zrevrange = AsyncMock(side_effect=mock_zrevrange)
        return mock_client
        
    @pytest.fixture
    def mock_redis(self, mock_redis_client):
        """Create a mock Redis class that returns our mock client"""
        mock_redis = MagicMock()
        mock_redis.from_pool.return_value = mock_redis_client
        with patch('redis.asyncio.Redis', mock_redis):
            yield mock_redis

    @pytest_asyncio.fixture
    async def storage(self, mock_redis, mock_redis_client) -> AsyncGenerator[RedisStorage, None]:
        """Create a RedisStorage instance with a mock Redis client"""
        storage = RedisStorage("redis://test")
        # Ensure the client is initialized
        storage.redis_client = mock_redis_client
        yield storage
        await storage.close()

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_ascending(self, storage, mock_redis_client):
        """Test getting a range from a sorted set in ascending order"""
        # Setup
        mock_redis_client.zrange = AsyncMock(return_value=[b"item1", b"item2", b"item3"])
        
        # Test
        result = await storage.get_sorted_set_range("test:key", 0, 2, desc=False)
    
        # Assert
        mock_redis_client.zrange.assert_awaited_once_with(
            name="test:key",
            start=0,
            end=2,
            withscores=False,
            encoding='utf-8'
        )
        assert result == ["item1", "item2", "item3"]

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_descending(self, storage, mock_redis_client):
        """Test getting a range from a sorted set in descending order"""
        # Setup
        mock_redis_client.zrevrange = AsyncMock(return_value=[b"item3", b"item2", b"item1"])
        
        # Test
        result = await storage.get_sorted_set_range("test:key", 0, 2, desc=True)
    
        # Assert
        mock_redis_client.zrevrange.assert_awaited_once_with(
            name="test:key",
            start=0,
            end=2,
            withscores=False,
            encoding='utf-8'
        )
        assert result == ["item3", "item2", "item1"]

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_with_scores(self, storage, mock_redis_client):
        """Test getting a range with scores from a sorted set"""
        # Setup
        test_data = [
            (b"item1", 1.0),
            (b"item2", 2.0),
            (b"item3", 3.0)
        ]
        mock_redis_client.zrange = AsyncMock(return_value=test_data)
        
        # Test
        result = await storage.get_sorted_set_range(
            "test:key", 0, 2, with_scores=True, desc=False
        )
    
        # Assert
        mock_redis_client.zrange.assert_awaited_once_with(
            name="test:key",
            start=0,
            end=2,
            withscores=True,
            encoding='utf-8'
        )
        assert result == [("item1", 1.0), ("item2", 2.0), ("item3", 3.0)]

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_empty(self, storage, mock_redis):
        """Test getting a range from an empty sorted set"""
        # Override the mock to return empty list
        async def mock_empty_zrange(*args, **kwargs):
            return []
            
        mock_redis.from_pool.return_value.zrange = mock_empty_zrange
        
        # Test
        result = await storage.get_sorted_set_range("empty:key", 0, 10)
        
        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_error(self, storage, mock_redis):
        """Test error handling when getting a range from a sorted set"""
        # Override the mock to raise an exception
        async def mock_error_zrange(*args, **kwargs):
            raise Exception("Redis error")
            
        mock_redis.from_pool.return_value.zrange = mock_error_zrange
        
        # Test and assert
        result = await storage.get_sorted_set_range("error:key", 0, 10)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_edge_cases(self, storage, mock_redis):
        """Test edge cases for sorted set range retrieval"""
        # Override the mock to return a fixed list
        async def mock_fixed_zrange(*args, **kwargs):
            return [b"item1", b"item2"]
            
        mock_redis.from_pool.return_value.zrange = mock_fixed_zrange
        
        # Test with negative indices
        result = await storage.get_sorted_set_range("test:key", -10, -1)
        assert result == ["item1", "item2"]
        
        # Test with start > stop
        result = await storage.get_sorted_set_range("test:key", 5, 1)
        assert result == ["item1", "item2"]
        
        # Test with large range
        result = await storage.get_sorted_set_range("test:key", 0, 1000)
        assert result == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_get_sorted_set_range_with_special_chars(self, storage, mock_redis):
        """Test getting a range with special characters in keys and values"""
        # Override the mock to return special characters
        async def mock_special_zrange(*args, **kwargs):
            return [
                (b"item:with:colons", 1.0),
                (b"item/with/slashes", 2.0),
                (b"item.with.dots", 3.0)
            ]
            
        mock_redis.from_pool.return_value.zrange = mock_special_zrange
        
        # Test with special characters in key
        result = await storage.get_sorted_set_range(
            "test:key:with:special:chars", 0, 2, with_scores=True
        )
        # Assert
        assert result == [
            ("item:with:colons", 1.0),
            ("item/with/slashes", 2.0),
            ("item.with.dots", 3.0)
        ]
