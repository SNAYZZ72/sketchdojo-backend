"""
Unit tests for WebtoonRepositoryRedis.
"""
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pytest_mock import MockerFixture

from app.domain.entities.webtoon import Webtoon
from app.domain.mappers.webtoon_mapper import WebtoonDataMapper
from app.infrastructure.repositories.webtoon_repository_redis import WebtoonRepositoryRedis
from app.infrastructure.utils.webtoon_keys import webtoon_key, webtoon_list_key, webtoon_user_webtoons_key

# Test data
TEST_WEBTOON_ID = uuid4()
TEST_USER_ID = uuid4()
TEST_WEBTOON_DATA = {
    "id": str(TEST_WEBTOON_ID),
    "title": "Test Webtoon",
    "description": "A test webtoon",
    "art_style": "webtoon",
    "created_at": "2023-01-01T00:00:00+00:00",
    "updated_at": "2023-01-01T00:00:00+00:00",
    "is_published": False,
    "metadata": {"creator_id": str(TEST_USER_ID)},
    "panels": [],
    "characters": []
}

# Fixtures

@pytest.fixture
def mock_storage():
    """Create a mock storage provider."""
    storage = MagicMock()
    storage.get = AsyncMock()
    storage.set = AsyncMock(return_value=True)
    storage.delete = AsyncMock(return_value=True)
    storage.sadd = AsyncMock(return_value=1)
    storage.srem = AsyncMock(return_value=1)
    storage.smembers = AsyncMock(return_value=set())
    storage.pipeline = MagicMock(return_value=storage)
    storage.execute = AsyncMock(return_value=[])
    storage.expire = AsyncMock(return_value=True)
    return storage

@pytest.fixture
def webtoon_repo(mock_storage):
    """Create a WebtoonRepositoryRedis instance with a mock storage."""
    return WebtoonRepositoryRedis(storage=mock_storage)

@pytest.fixture
def sample_webtoon():
    """Create a sample Webtoon instance for testing."""
    return Webtoon(
        id=TEST_WEBTOON_ID,
        title="Test Webtoon",
        description="A test webtoon",
        metadata={"creator_id": str(TEST_USER_ID)}
    )

# Test cases

class TestWebtoonRepositoryRedis:
    """Test cases for WebtoonRepositoryRedis."""

    async def test_save_webtoon(self, webtoon_repo, mock_storage, sample_webtoon):
        """Test saving a webtoon."""
        # Execute
        saved_webtoon = await webtoon_repo.save(sample_webtoon)
        
        # Assert
        assert saved_webtoon is not None
        assert saved_webtoon.id == sample_webtoon.id
        
        # Check that set was called with the correct arguments
        mock_storage.set.assert_awaited_once()
        args, _ = mock_storage.set.await_args_list[0]
        assert args[0] == webtoon_key(sample_webtoon.id)
        
        # Check that the webtoon was added to the global set
        mock_storage.sadd.assert_any_await(webtoon_list_key(), str(sample_webtoon.id))
        
        # Check that the webtoon was added to the user's set
        mock_storage.sadd.assert_any_await(
            webtoon_user_webtoons_key(TEST_USER_ID),
            str(sample_webtoon.id)
        )
        
        # Check that expire was called
        mock_storage.expire.assert_awaited_once()

    async def test_get_by_id_found(self, webtoon_repo, mock_storage, sample_webtoon):
        """Test getting a webtoon by ID when it exists."""
        # Setup
        mock_storage.get.return_value = json.dumps(TEST_WEBTOON_DATA)
        
        # Execute
        result = await webtoon_repo.get_by_id(TEST_WEBTOON_ID)
        
        # Assert
        assert result is not None
        assert result.id == TEST_WEBTOON_ID
        assert result.title == "Test Webtoon"
        mock_storage.get.assert_awaited_once_with(webtoon_key(TEST_WEBTOON_ID))

    async def test_get_by_id_not_found(self, webtoon_repo, mock_storage):
        """Test getting a webtoon by ID when it doesn't exist."""
        # Setup
        mock_storage.get.return_value = None
        
        # Execute
        result = await webtoon_repo.get_by_id(TEST_WEBTOON_ID)
        
        # Assert
        assert result is None
        mock_storage.get.assert_awaited_once_with(webtoon_key(TEST_WEBTOON_ID))

    async def test_get_by_creator(self, webtoon_repo, mock_storage, sample_webtoon):
        """Test getting webtoons by creator."""
        # Setup
        mock_storage.smembers.return_value = {str(TEST_WEBTOON_ID)}
        mock_storage.get.return_value = json.dumps(TEST_WEBTOON_DATA)
        
        # Execute
        webtoons = await webtoon_repo.get_by_creator(TEST_USER_ID)
        
        # Assert
        assert len(webtoons) == 1
        assert webtoons[0].id == TEST_WEBTOON_ID
        mock_storage.smembers.assert_awaited_once_with(webtoon_user_webtoons_key(TEST_USER_ID))
        mock_storage.get.assert_awaited_once_with(webtoon_key(TEST_WEBTOON_ID))

    async def test_get_all(self, webtoon_repo, mock_storage, sample_webtoon):
        """Test getting all webtoons with pagination."""
        # Setup
        mock_storage.smembers.return_value = {str(TEST_WEBTOON_ID)}
        mock_storage.get.return_value = json.dumps(TEST_WEBTOON_DATA)
        
        # Execute
        webtoons = await webtoon_repo.get_all(skip=0, limit=10)
        
        # Assert
        assert len(webtoons) == 1
        assert webtoons[0].id == TEST_WEBTOON_ID
        mock_storage.smembers.assert_awaited_once_with(webtoon_list_key())

    async def test_delete(self, webtoon_repo, mock_storage, sample_webtoon, mocker):
        """Test deleting a webtoon."""
        # Setup
        mock_storage.delete.return_value = True
        
        # Mock get_by_id to return our sample webtoon
        mocker.patch.object(webtoon_repo, 'get_by_id', return_value=sample_webtoon)
        
        # Execute
        result = await webtoon_repo.delete(TEST_WEBTOON_ID)
        
        # Assert
        assert result is True
        webtoon_repo.get_by_id.assert_awaited_once_with(TEST_WEBTOON_ID)
        mock_storage.delete.assert_awaited_once_with(webtoon_key(TEST_WEBTOON_ID))
        mock_storage.srem.assert_any_await(webtoon_list_key(), str(TEST_WEBTOON_ID))
        
        # Verify we also remove from the creator's webtoons set
        mock_storage.srem.assert_any_await(
            webtoon_user_webtoons_key(TEST_USER_ID),
            str(TEST_WEBTOON_ID)
        )

    async def test_update_fields(self, webtoon_repo, mock_storage, sample_webtoon):
        """Test updating specific fields of a webtoon."""
        # Setup
        mock_storage.get.return_value = json.dumps(TEST_WEBTOON_DATA)
        
        # Execute
        updated_webtoon = await webtoon_repo.update_fields(
            entity_id=TEST_WEBTOON_ID,
            data={"title": "Updated Title", "is_published": True}
        )
        
        # Assert
        assert updated_webtoon is not None
        assert updated_webtoon.title == "Updated Title"
        assert updated_webtoon.is_published is True
        
        # Check that set was called with the updated data
        mock_storage.set.assert_awaited_once()
        args, _ = mock_storage.set.await_args_list[0]
        assert args[0] == webtoon_key(TEST_WEBTOON_ID)
        assert json.loads(args[1])["title"] == "Updated Title"
        
        # Check that expire was called
        mock_storage.expire.assert_awaited_once()
