# tests/unit/test_task_repository.py
"""
Tests for TaskRepository
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from uuid import UUID

from app.domain.entities.generation_task import (
    GenerationTask, 
    TaskProgress,
    TaskStatus,
    TaskType
)
from app.domain.mappers.task_mapper import TaskDataMapper
from app.domain.repositories.task_repository import TaskRepository


class MockStorageProvider:
    """Mock implementation of a storage provider for testing"""

    def __init__(self):
        self.store_data = {}
        self.store = AsyncMock(return_value=True)
        self.retrieve = AsyncMock(side_effect=self._mock_retrieve)
        self.delete = AsyncMock(return_value=True)
        self.exists = AsyncMock(return_value=True)
        self.list_keys = AsyncMock(return_value=["task:123", "task:456"])
        
    async def _mock_retrieve(self, key):
        """Mock retrieve method that returns preset data based on key"""
        if key == "task:not-found":
            return None
        elif key == "task:error":
            raise Exception("Storage error")
        else:
            return {"id": key.split(":")[-1], "task_type": "GENERATE_STORY"}


class TestTaskRepository:
    """Test TaskRepository functionality"""

    def setup_method(self):
        """Initialize test data and repository"""
        self.storage = MockStorageProvider()
        self.mapper = MagicMock(spec=TaskDataMapper)
        self.repository = TaskRepository(self.storage, self.mapper)
        self.task_id = uuid.uuid4()
        
        # Create a sample progress
        progress = TaskProgress(
            current_step=1, 
            total_steps=5,
            current_operation="Processing",
            percentage=20
        )
        
        # Create a sample task
        self.task = GenerationTask(
            id=self.task_id,
            task_type=TaskType.STORY_GENERATION,
            status=TaskStatus.PROCESSING,
            progress=progress,
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=None,
            error_message=None,
            result={},
            input_data={"title": "Test Story"},
            metadata={"user_id": "user123"},
        )
        
        # Configure mapper mock
        self.mapper.to_dict.return_value = {
            "id": str(self.task_id), 
            "task_type": TaskType.STORY_GENERATION.value,
            "status": TaskStatus.PROCESSING.value
        }
        self.mapper.from_dict.return_value = self.task

    @pytest.mark.asyncio
    async def test_save(self):
        """Test saving a task"""
        # Call save method
        result = await self.repository.save(self.task)
        
        # Check results
        assert result == self.task
        self.mapper.to_dict.assert_called_once_with(self.task)
        self.storage.store.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_save_error(self):
        """Test saving a task with storage error"""
        # Configure storage to fail
        self.storage.store.return_value = False
        
        # Call save method and check exception
        with pytest.raises(RuntimeError):
            await self.repository.save(self.task)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting a task by ID"""
        # Call get_by_id method
        result = await self.repository.get_by_id(self.task_id)
        
        # Check results
        assert result == self.task
        self.storage.retrieve.assert_called_once()
        self.mapper.from_dict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting a non-existent task"""
        # Configure storage to return None for not-found key
        self.storage.retrieve = AsyncMock(return_value=None)
        
        # Call get_by_id method
        result = await self.repository.get_by_id(uuid.uuid4())
        
        # Check result is None
        assert result is None
        
    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test getting all tasks"""
        # Configure storage and mapper for get_all
        self.storage.list_keys.return_value = [f"task:{self.task_id}"]
        
        # Call get_all method
        results = await self.repository.get_all()
        
        # Check results
        assert len(results) == 1
        assert results[0] == self.task
        self.storage.list_keys.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting a task"""
        # Call delete method
        result = await self.repository.delete(self.task_id)
        
        # Check result
        assert result is True
        self.storage.delete.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if a task exists"""
        # Call exists method
        result = await self.repository.exists(self.task_id)
        
        # Check result
        assert result is True
        self.storage.exists.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_update_fields(self):
        """Test updating specific fields of a task"""
        # Setup test data
        update_data = {"status": TaskStatus.COMPLETED.value, "progress": {"percentage": 100}}
        
        # Configure storage to return our task
        self.storage.retrieve = AsyncMock(return_value={"id": str(self.task_id)})
        
        # Call update_fields method
        result = await self.repository.update_fields(self.task_id, update_data)
        
        # Check results - our mocked mapper will return the original task
        assert result == self.task
        self.storage.retrieve.assert_called_once()
        self.storage.store.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_pending_tasks(self):
        """Test getting pending tasks"""
        # Create mock tasks with different statuses
        task1 = MagicMock(spec=GenerationTask)
        task1.status = TaskStatus.PENDING
        task1.task_type = TaskType.STORY_GENERATION
        task1.is_terminal = False  # Not terminal
        
        task2 = MagicMock(spec=GenerationTask)
        task2.status = TaskStatus.COMPLETED
        task2.task_type = TaskType.STORY_GENERATION
        task2.is_terminal = True  # Terminal status
        
        task3 = MagicMock(spec=GenerationTask)
        task3.status = TaskStatus.PENDING
        task3.task_type = TaskType.PANEL_GENERATION
        task3.is_terminal = False  # Not terminal
        
        # Replace get_all with a mock that returns our test data
        with patch.object(self.repository, 'get_all', new=AsyncMock(return_value=[task1, task2, task3])):
            # Call get_active_tasks method
            results = await self.repository.get_active_tasks()
            
            # Check results
            assert len(results) == 2
            # Both pending tasks should be included (task1 and task3)
            assert task1 in results
            assert task3 in results
            assert task2 not in results  # The completed task should not be included
