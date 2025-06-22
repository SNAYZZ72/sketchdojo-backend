# tests/unit/test_webtoon_repository.py
"""
Tests for WebtoonRepository
"""
import copy
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.webtoon import Webtoon
from app.domain.entities.character import Character
from app.domain.entities.panel import Panel
from app.domain.mappers.webtoon_mapper import WebtoonDataMapper
from app.domain.repositories.webtoon_repository import WebtoonRepository


class MockStorageProvider:
    """Mock implementation of a storage provider for testing"""

    def __init__(self):
        self.store_data = {}
        self.store = AsyncMock(return_value=True)
        self.retrieve = AsyncMock(side_effect=self._mock_retrieve)
        self.delete = AsyncMock(return_value=True)
        self.exists = AsyncMock(return_value=True)
        self.list_keys = AsyncMock(return_value=["webtoon:123", "webtoon:456"])
        
    async def _mock_retrieve(self, key):
        """Mock retrieve method that returns preset data based on key"""
        if key == "webtoon:not-found":
            return None
        elif key == "webtoon:error":
            raise Exception("Storage error")
        else:
            return {"id": key.split(":")[-1], "title": "Test Webtoon"}


class TestWebtoonRepository:
    """Test WebtoonRepository functionality"""

    def setup_method(self):
        """Initialize test data and mocks"""
        # Create a mock for the storage provider
        self.storage = AsyncMock(spec=StorageProvider)
        self.storage.store = AsyncMock(return_value=True)
        self.storage.retrieve = AsyncMock(return_value=None)
        self.storage.delete = AsyncMock(return_value=True)
        self.storage.exists = AsyncMock(return_value=True)
        self.storage.list_keys = AsyncMock(return_value=["webtoon:123", "webtoon:456"])

        # Create a mocked mapper
        self.mapper = MagicMock(spec=WebtoonDataMapper)
        
        # Create the repository with mocked storage
        self.repository = WebtoonRepository(
            storage=self.storage,
            mapper=self.mapper
        )
        
        # Create a sample webtoon for testing
        self.webtoon_id = uuid.uuid4()
        self.webtoon = Webtoon(
            id=self.webtoon_id,
            title="Test Webtoon",
            description="A test webtoon",
            art_style="webtoon",
            panels=[],
            characters=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_published=False,
            metadata={"tags": ["test", "sample"]},
        )
        
        # Set up mapper mocks
        self.mapper.to_dict.return_value = {"id": str(self.webtoon_id), "title": "Test Webtoon"}
        self.mapper.from_dict.return_value = self.webtoon

    @pytest.mark.asyncio
    async def test_save(self):
        """Test saving a webtoon"""
        # Call save method
        result = await self.repository.save(self.webtoon)
        
        # Check result is the webtoon and storage was called
        assert result == self.webtoon
        self.storage.store.assert_called_once()
        self.mapper.to_dict.assert_called_once_with(self.webtoon)

    @pytest.mark.asyncio
    async def test_save_error(self):
        """Test error handling when saving a webtoon"""
        # Configure storage to fail
        self.storage.store.side_effect = Exception("Connection error")
        
        # Call save method and check exception
        with pytest.raises(Exception):
            await self.repository.save(self.webtoon)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting a webtoon by ID"""
        # Configure storage to return data
        webtoon_data = {"id": str(self.webtoon_id), "title": "Test Webtoon"}
        self.storage.retrieve.return_value = webtoon_data
        
        # Call get_by_id method
        webtoon = await self.repository.get_by_id(self.webtoon_id)
        
        # Check results
        assert webtoon == self.webtoon
        self.storage.retrieve.assert_called_once()
        self.mapper.from_dict.assert_called_once_with(webtoon_data)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting a non-existent webtoon"""
        # Configure storage to return None for not-found key
        self.storage.retrieve.return_value = None
        
        # Call get_by_id method
        test_id = uuid.uuid4()
        result = await self.repository.get_by_id(test_id)
        
        # Check result is None
        assert result is None
        self.storage.retrieve.assert_called_once_with(f"webtoon:{str(test_id)}")

    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test getting all webtoons"""
        # Configure storage to return keys and data
        webtoon_keys = [f"webtoon:{self.webtoon_id}"]
        self.storage.list_keys.return_value = webtoon_keys
        webtoon_data = {"id": str(self.webtoon_id), "title": "Test Webtoon"}
        self.storage.retrieve.return_value = webtoon_data
        
        # Call get_all method
        results = await self.repository.get_all()
        
        # Check results
        assert len(results) == 1
        assert results[0] == self.webtoon
        self.storage.list_keys.assert_called_once_with("webtoon:*")
        self.storage.retrieve.assert_called_once_with(webtoon_keys[0])

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting a webtoon"""
        # Configure storage to return success
        self.storage.delete.return_value = True
        
        # Call delete method
        result = await self.repository.delete(self.webtoon_id)
        
        # Check result
        assert result is True
        self.storage.delete.assert_called_once_with(f"webtoon:{self.webtoon_id}")

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if a webtoon exists"""
        # Configure storage to return True for exists
        self.storage.exists.return_value = True
        
        # Call exists method
        result = await self.repository.exists(self.webtoon_id)
        
        # Check result
        assert result is True
        self.storage.exists.assert_called_once_with(f"webtoon:{self.webtoon_id}")

    @pytest.mark.asyncio
    async def test_update_fields(self):
        """Test updating specific fields of a webtoon"""
        # Setup test data
        update_data = {"title": "Updated Title", "is_published": True}
        
        # Configure storage to return our webtoon data
        webtoon_data = {"id": str(self.webtoon_id), "title": "Test Webtoon"}
        self.storage.retrieve.return_value = webtoon_data
        
        # Update the from_dict mock to return an updated webtoon
        updated_webtoon = copy.deepcopy(self.webtoon)
        updated_webtoon.title = "Updated Title"
        updated_webtoon.is_published = True
        self.mapper.from_dict.return_value = updated_webtoon
        
        # Call update_fields method
        result = await self.repository.update_fields(self.webtoon_id, update_data)
        
        # Check results
        assert result == updated_webtoon
        self.storage.retrieve.assert_called_once_with(f"webtoon:{self.webtoon_id}")
        self.storage.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_published(self):
        """Test getting published webtoons"""
        # Create test webtoons with different published states
        published_webtoon = copy.deepcopy(self.webtoon)
        published_webtoon.is_published = True
        
        # Setup the get_all mock to simulate filtering by is_published=True
        mock_get_all = AsyncMock()
        mock_get_all.return_value = [published_webtoon]  # Return only published webtoons
        
        # Patch the get_all method to verify it's called with is_published=True
        with patch.object(self.repository, 'get_all', mock_get_all):
            # Call get_published method
            results = await self.repository.get_published()
            
            # Check results
            assert len(results) == 1
            assert results[0] == published_webtoon
            assert results[0].is_published is True
            mock_get_all.assert_called_once_with(is_published=True)
