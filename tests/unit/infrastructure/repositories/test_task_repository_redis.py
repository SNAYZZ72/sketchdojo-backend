"""
Tests for the TaskRepositoryRedis implementation.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.domain.entities.generation_task import GenerationTask, TaskType, TaskStatus
from app.application.interfaces.storage_provider import StorageProvider
from app.domain.mappers.task_mapper import TaskDataMapper
from app.infrastructure.repositories.task_repository_redis import TaskRepositoryRedis
from app.infrastructure.utils.task_keys import task_key, task_user_tasks_key

# Fixtures

@pytest.fixture
def mock_storage():
    """Create a mock storage provider"""
    storage = MagicMock(spec=StorageProvider)
    storage.set = AsyncMock(return_value=True)
    storage.get = AsyncMock()
    storage.delete = AsyncMock(return_value=True)
    storage.exists = AsyncMock(return_value=False)
    storage.sadd = AsyncMock(return_value=1)
    storage.srem = AsyncMock(return_value=1)
    storage.smembers = AsyncMock(return_value=set())
    storage.expire = AsyncMock(return_value=True)  # Add expire mock
    return storage

@pytest.fixture
def task_mapper() -> TaskDataMapper:
    """Create a task data mapper."""
    return TaskDataMapper()

@pytest.fixture
def task_repo(mock_storage: StorageProvider, task_mapper: TaskDataMapper) -> TaskRepositoryRedis:
    """Create a task repository with mock storage."""
    return TaskRepositoryRedis(storage=mock_storage, mapper=task_mapper)

@pytest_asyncio.fixture
async def sample_task() -> GenerationTask:
    """Create a sample task for testing."""
    task = GenerationTask()
    task.id = uuid4()
    task.task_type = TaskType.IMAGE_GENERATION
    task.status = TaskStatus.PENDING
    task.input_data = {"prompt": "test prompt", "user_id": str(uuid4())}
    task.created_at = datetime.now(timezone.utc)
    return task

# Tests

@pytest.mark.asyncio
class TestTaskRepositoryRedis:
    """Test cases for TaskRepositoryRedis."""
    
    async def test_save_task(self, task_repo: TaskRepositoryRedis, sample_task: GenerationTask, mock_storage: MagicMock):
        """Test saving a task."""
        # Setup
        task_data = {
            "id": str(sample_task.id),
            "task_type": sample_task.task_type.value,
            "status": sample_task.status.value,
            "input_data": sample_task.input_data,
            "created_at": sample_task.created_at.isoformat(),
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "result": None,
            "metadata": {},
            "progress": {
                "current_step": 0,
                "total_steps": 0,
                "current_operation": "",
                "percentage": 0.0
            }
        }
        
        # Execute
        saved_task = await task_repo.save(sample_task)
        
        # Assert
        assert saved_task is not None
        assert saved_task.id == sample_task.id
        mock_storage.set.assert_awaited_once()
        mock_storage.expire.assert_awaited_once()
        user_id = sample_task.input_data.get("user_id")
        mock_storage.sadd.assert_awaited_once_with(
            task_user_tasks_key(user_id),
            str(sample_task.id)
        )
        # Check that set was called with the correct arguments
        args, _ = mock_storage.set.await_args_list[0]
        assert args[0] == task_key(sample_task.id)
        stored_data = json.loads(args[1])
        assert stored_data["id"] == str(sample_task.id)
        assert stored_data["task_type"] == sample_task.task_type.value
        assert stored_data["status"] == sample_task.status.value
        assert stored_data["input_data"] == sample_task.input_data
        
        # Check that expire was called with the correct TTL
        mock_storage.expire.assert_awaited_once()
        expire_args, _ = mock_storage.expire.await_args_list[0]
        assert expire_args[0] == task_key(sample_task.id)
        assert expire_args[1] == 604800  # 7 days in seconds
        # Check that the task was added to the user's task list
        user_id = sample_task.input_data.get("user_id")
        if user_id:
            mock_storage.sadd.assert_awaited_with(
                task_user_tasks_key(user_id),
                str(sample_task.id)
            )
    
    async def test_get_by_id_found(self, task_repo: TaskRepositoryRedis, sample_task: GenerationTask, mock_storage: MagicMock, task_mapper: TaskDataMapper):
        """Test getting a task by ID when it exists."""
        # Setup
        task_data = task_mapper.to_dict(sample_task)
        mock_storage.get.return_value = json.dumps(task_data)
        
        # Execute
        result = await task_repo.get_by_id(sample_task.id)
        
        # Assert
        assert result is not None
        assert result.id == sample_task.id
        mock_storage.get.assert_awaited_once_with(task_key(sample_task.id))
    
    async def test_get_by_id_not_found(self, task_repo: TaskRepositoryRedis, mock_storage: MagicMock):
        """Test getting a task by ID when it doesn't exist."""
        # Setup
        mock_storage.get.return_value = None
        task_id = uuid4()
        
        # Execute
        result = await task_repo.get_by_id(task_id)
        
        # Assert
        assert result is None
        mock_storage.get.assert_awaited_once_with(task_key(task_id))
    
    async def test_get_by_user(
        self, 
        task_repo: TaskRepositoryRedis, 
        sample_task: GenerationTask, 
        mock_storage: MagicMock, 
        task_mapper: TaskDataMapper
    ):
        """Test getting tasks for a user."""
        # Setup
        user_id = sample_task.input_data.get("user_id")
        task_data = task_mapper.to_dict(sample_task)
        mock_storage.smembers.return_value = [str(sample_task.id)]
        mock_storage.get.side_effect = [json.dumps(task_data)]
        
        # Execute
        tasks = await task_repo.get_by_user(
            user_id=user_id,
            status=TaskStatus.PENDING,
            task_type=TaskType.IMAGE_GENERATION,
            limit=10,
            offset=0
        )
        
        # Assert
        assert len(tasks) == 1
        assert tasks[0].id == sample_task.id
        mock_storage.smembers.assert_awaited_once_with(task_user_tasks_key(user_id))
        mock_storage.get.assert_awaited_once_with(task_key(sample_task.id))
    
    async def test_delete_task(self, task_repo: TaskRepositoryRedis, sample_task: GenerationTask, mock_storage: MagicMock, task_mapper: TaskDataMapper):
        """Test deleting a task."""
        # Setup
        user_id = sample_task.input_data.get("user_id")
        task_data = task_mapper.to_dict(sample_task)
        mock_storage.get.return_value = json.dumps(task_data)
        mock_storage.delete.return_value = True
        
        # Execute
        result = await task_repo.delete(sample_task.id)
        
        # Assert
        assert result is True
        mock_storage.delete.assert_awaited_with(task_key(sample_task.id))
        mock_storage.srem.assert_awaited_with(
            task_user_tasks_key(user_id),
            str(sample_task.id)
        )
    
    async def test_delete_task_not_found(self, task_repo: TaskRepositoryRedis, mock_storage: MagicMock):
        """Test deleting a task that doesn't exist."""
        # Setup
        mock_storage.get.return_value = None
        task_id = uuid4()
        
        # Execute
        result = await task_repo.delete(task_id)
        
        # Assert
        assert result is False
        mock_storage.get.assert_awaited_once_with(task_key(task_id))
        mock_storage.delete.assert_not_awaited()
        mock_storage.srem.assert_not_awaited()
    
    async def test_update_fields(self, task_repo: TaskRepositoryRedis, sample_task: GenerationTask, mock_storage: MagicMock, task_mapper: TaskDataMapper):
        """Test updating specific fields of a task."""
        # Setup - initial task data
        initial_data = task_mapper.to_dict(sample_task)
        mock_storage.get.return_value = json.dumps(initial_data)
        
        # New status and result
        new_status = TaskStatus.COMPLETED
        new_result = {"image_url": "https://example.com/image.jpg"}
        
        # Execute
        updated_task = await task_repo.update_fields(
            entity_id=sample_task.id,
            data={"status": new_status, "result": new_result}
        )
        
        # Assert
        assert updated_task is not None
        assert updated_task.status == new_status
        assert updated_task.result == new_result
        
        # Check that storage.set was called with the updated data
        args, _ = mock_storage.set.await_args_list[0]
        assert args[0] == task_key(sample_task.id)
        stored_data = json.loads(args[1])
        assert stored_data["id"] == str(sample_task.id)
        assert stored_data["status"] == new_status.value
        assert stored_data["result"] == new_result
        
        # Check that expire was called with the correct TTL
        mock_storage.expire.assert_awaited_once()
        expire_args, _ = mock_storage.expire.await_args_list[0]
        assert expire_args[0] == task_key(sample_task.id)
        assert expire_args[1] == 604800  # 7 days in seconds
