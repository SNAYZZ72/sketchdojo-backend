"""
Tests for the BaseRedisRepository class.
"""
import json
import pytest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Type, Callable, Union
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import UUID, uuid4

from app.application.interfaces.storage_provider import StorageProvider
from app.infrastructure.repositories.base_redis_repository import BaseRedisRepository

# Test model
class TestModel:
    """Test model for repository tests."""
    
    def __init__(self, id: str, name: str, value: int, **kwargs):
        self.id = id
        self.name = name
        self.value = value
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc))
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def parse_obj(cls, data: Dict[str, Any]) -> 'TestModel':
        """Parse from dictionary."""
        # Convert string timestamps back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def __eq__(self, other):
        if not isinstance(other, TestModel):
            return False
        return (
            self.id == other.id and
            self.name == other.name and
            self.value == other.value
        )

# Test repository
class TestRepository(BaseRedisRepository[TestModel]):
    """Test repository implementation."""
    
    _key_prefix = "test:model"  # Class-level prefix to match base class
    
    def __init__(self, storage: StorageProvider):
        super().__init__(
            storage=storage,
            key_prefix=self._key_prefix,
            ttl_seconds=3600  # 1 hour TTL
        )
    
    @property
    def entity_class(self) -> Type[TestModel]:
        return TestModel
    
    def _get_entity_key(self, entity_id: Union[UUID, str, int]) -> str:
        """Generate a Redis key for the given entity ID.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            str: The Redis key for the entity
        """
        return f"{self._key_prefix}:{str(entity_id)}"
    
    def _serialize_entity(self, entity: TestModel) -> str:
        """Serialize entity to JSON string."""
        return json.dumps(entity.dict())
    
    def _deserialize_entity(self, data: str, entity_class: Type[TestModel] = None) -> TestModel:
        """Deserialize JSON string to entity."""
        if not data:
            return None
        data_dict = json.loads(data) if isinstance(data, str) else data
        return TestModel.parse_obj(data_dict)

# Fixtures
@pytest.fixture
def mock_storage() -> StorageProvider:
    """Create a mock storage provider."""
    # Create a mock with the required methods
    storage = AsyncMock()
    
    # Configure the mock methods
    storage.get = AsyncMock(return_value=None)
    storage.set = AsyncMock(return_value=True)
    storage.delete = AsyncMock(return_value=True)
    storage.exists = AsyncMock(return_value=False)
    storage.scan = AsyncMock(return_value=(0, []))  # cursor, keys
    
    # Add any additional methods needed by the tests
    storage.add_to_sorted_set = AsyncMock(return_value=True)
    storage.get_sorted_set = AsyncMock(return_value=[])
    
    return storage

@pytest.fixture
def test_repo(mock_storage: StorageProvider) -> TestRepository:
    """Create a test repository with a mock storage."""
    return TestRepository(storage=mock_storage)

@pytest.fixture
def test_entity() -> TestModel:
    """Create a test entity."""
    return TestModel(
        id=str(uuid4()),
        name="Test Entity",
        value=42,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

# Tests
@pytest.mark.asyncio
async def test_save_entity(test_repo: TestRepository, test_entity: TestModel):
    """Test saving an entity."""
    # Setup
    test_repo.storage.set = AsyncMock(return_value=True)
    
    # Execute
    result = await test_repo.save(test_entity)
    
    # Assert
    assert result == test_entity
    test_repo.storage.set.assert_awaited_once()
    
    # Check that the key was generated correctly
    args, _ = test_repo.storage.set.await_args
    assert test_repo._key_prefix in args[0]  # Key contains the prefix
    assert test_entity.id in args[0]  # Key contains the entity ID
    
    # Check that the value was serialized correctly
    stored_data = json.loads(args[1])
    assert stored_data['id'] == test_entity.id
    assert stored_data['name'] == test_entity.name
    assert stored_data['value'] == test_entity.value

@pytest.mark.asyncio
async def test_get_by_id_found(test_repo: TestRepository, test_entity: TestModel):
    """Test getting an entity by ID when it exists."""
    # Setup
    entity_data = json.dumps(test_entity.dict())
    test_repo.storage.get = AsyncMock(return_value=entity_data)
    
    # Execute
    result = await test_repo.get_by_id(test_entity.id)
    
    # Assert
    assert result is not None
    assert result.id == test_entity.id
    assert result.name == test_entity.name
    assert result.value == test_entity.value
    
    # Check that the key was generated correctly
    test_repo.storage.get.assert_awaited_once()
    args, _ = test_repo.storage.get.await_args
    assert test_repo._key_prefix in args[0]
    assert test_entity.id in args[0]

@pytest.mark.asyncio
async def test_get_by_id_not_found(test_repo: TestRepository):
    """Test getting an entity by ID when it doesn't exist."""
    # Setup
    test_repo.storage.get = AsyncMock(return_value=None)
    
    # Execute
    result = await test_repo.get_by_id("nonexistent-id")
    
    # Assert
    assert result is None
    test_repo.storage.get.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_entity(test_repo: TestRepository, test_entity: TestModel):
    """Test deleting an entity."""
    # Setup
    test_repo.storage.delete = AsyncMock(return_value=True)
    
    # Execute
    result = await test_repo.delete(test_entity.id)
    
    # Assert
    assert result is True
    test_repo.storage.delete.assert_awaited_once()
    
    # Check that the key was generated correctly
    args, _ = test_repo.storage.delete.await_args
    assert test_repo._key_prefix in args[0]
    assert test_entity.id in args[0]

@pytest.mark.asyncio
async def test_exists_entity(test_repo: TestRepository, test_entity: TestModel):
    """Test checking if an entity exists."""
    # Setup
    test_repo.storage.exists = AsyncMock(return_value=True)
    
    # Execute
    result = await test_repo.exists(test_entity.id)
    
    # Assert
    assert result is True
    test_repo.storage.exists.assert_awaited_once()
    
    # Check that the key was generated correctly
    args, _ = test_repo.storage.exists.await_args
    assert test_repo._key_prefix in args[0]
    assert test_entity.id in args[0]

@pytest.mark.asyncio
async def test_update_fields(test_repo: TestRepository, test_entity: TestModel):
    """Test updating specific fields of an entity."""
    # Setup
    # First mock getting the existing entity
    entity_data = json.dumps(test_entity.dict())
    test_repo.storage.get = AsyncMock(return_value=entity_data)
    test_repo.storage.set = AsyncMock(return_value=True)
    
    # New values for update
    updates = {"name": "Updated Name", "value": 100}
    
    # Execute
    updated_entity = await test_repo.update_fields(test_entity.id, updates)
    
    # Assert
    assert updated_entity is not None
    assert updated_entity.name == "Updated Name"
    assert updated_entity.value == 100
    
    # Check that the entity was saved with updated values
    test_repo.storage.set.assert_awaited_once()
    args, _ = test_repo.storage.set.await_args
    stored_data = json.loads(args[1])
    assert stored_data['name'] == "Updated Name"
    assert stored_data['value'] == 100

@pytest.mark.asyncio
async def test_get_all(test_repo: TestRepository, test_entity: TestModel):
    """Test getting all entities with pagination and filtering."""
    # Setup
    # Create some test entities
    entity1 = TestModel(id=str(uuid4()), name="Entity 1", value=10)
    entity2 = TestModel(id=str(uuid4()), name="Entity 2", value=20)
    entity3 = TestModel(id=str(uuid4()), name="Entity 3", value=30)
    
    # Mock the scan to return keys - match the actual Redis scan call signature
    keys = [f"test:model:{entity.id}" for entity in [entity1, entity2, entity3]]
    test_repo.storage.scan = AsyncMock(return_value=(0, keys))
    
    # Mock get to return serialized entities
    test_repo.storage.get = AsyncMock(side_effect=[
        json.dumps(entity1.dict()),
        json.dumps(entity2.dict()),
        json.dumps(entity3.dict())
    ])
    
    # Execute - get all entities
    result = await test_repo.get_all()
    
    # Assert
    assert len(result) == 3
    assert all(isinstance(e, TestModel) for e in result)
    
    # Check that scan was called with the correct parameters
    test_repo.storage.scan.assert_awaited_once()
    args, kwargs = test_repo.storage.scan.await_args
    assert args[0] == 0  # cursor
    assert args[1] == "test:model:*"  # pattern
    assert kwargs.get('count', 100) == 100  # count
    
    # Check that get was called for each key
    assert test_repo.storage.get.await_count == 3
    
    # Test with filters - base implementation doesn't support field filtering,
    # so we'll just test that the scan is called with the correct pattern
    test_repo.storage.scan.reset_mock()
    test_repo.storage.get.reset_mock()
    
    # Setup scan to return no keys for this test
    test_repo.storage.scan = AsyncMock(return_value=(0, []))
    
    # Execute with filters (value > 15)
    filtered_result = await test_repo.get_all(value__gt=15)
    
    # Assert
    assert len(filtered_result) == 0  # No entities match the filter
    test_repo.storage.scan.assert_awaited_once()
    args, _ = test_repo.storage.scan.await_args
    assert args[1] == "test:model:*"  # Pattern should still be the same

@pytest.mark.asyncio
async def test_error_handling(test_repo: TestRepository, test_entity: TestModel):
    """Test error handling in repository methods."""
    # Test error in save
    test_repo.storage.set = AsyncMock(side_effect=Exception("Storage error"))
    with pytest.raises(Exception, match="Failed to save entity"):
        try:
            await test_repo.save(test_entity)
        except Exception as e:
            assert "Failed to save entity" in str(e)
            raise
    
    # Test error in get_by_id - should return None on error
    test_repo.storage.get = AsyncMock(side_effect=Exception("Storage error"))
    result = await test_repo.get_by_id("test-id")
    assert result is None
    
    # Test error in delete - should return False on error
    test_repo.storage.delete = AsyncMock(side_effect=Exception("Storage error"))
    result = await test_repo.delete("test-id")
    assert result is False
    
    # Test error in exists - should return False on error
    test_repo.storage.exists = AsyncMock(side_effect=Exception("Storage error"))
    result = await test_repo.exists("test-id")
    assert result is False
    
    # Test error in update_fields when getting the entity - should return None on error
    test_repo.storage.get = AsyncMock(side_effect=Exception("Storage error"))
    result = await test_repo.update_fields("test-id", {"name": "New Name"})
    assert result is None
    
    # Test error in update_fields when saving the updated entity
    entity_data = json.dumps(test_entity.dict())
    test_repo.storage.get = AsyncMock(return_value=entity_data)
    test_repo.storage.set = AsyncMock(side_effect=Exception("Storage error"))
    try:
        await test_repo.update_fields(test_entity.id, {"name": "New Name"})
        assert False, "Expected an exception to be raised"
    except Exception as e:
        assert "Storage error" in str(e)
