"""
Redis implementation of the TaskRepository using BaseRedisRepository
"""
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.generation_task import GenerationTask, TaskStatus, TaskType
from app.domain.mappers.task_mapper import TaskDataMapper
from app.domain.repositories.task_repository import TaskRepository as TaskRepositoryInterface
from app.infrastructure.repositories.base_redis_repository import BaseRedisRepository
from app.infrastructure.utils.task_keys import (
    task_key,
    task_user_tasks_key,
    task_pattern,
    task_user_tasks_pattern
)

logger = logging.getLogger(__name__)


def _json_dumps(data: Any) -> str:
    """Serialize data to JSON string."""
    return json.dumps(data)


def _json_loads(data: str) -> Any:
    """Deserialize JSON string to Python object."""
    return json.loads(data)


class TaskRepositoryRedis(BaseRedisRepository[GenerationTask], TaskRepositoryInterface):
    """Redis implementation of the TaskRepository"""

    def __init__(self, storage: StorageProvider, mapper: TaskDataMapper = None):
        super().__init__(
            storage=storage,
            key_prefix="task",
            ttl_seconds=86400 * 7  # 7 days TTL for tasks
        )
        self.mapper = mapper or TaskDataMapper()
        logger.info("TaskRepositoryRedis initialized")
        
    @property
    def entity_class(self) -> Type[GenerationTask]:
        return GenerationTask

    def _get_entity_key(self, entity_id: Union[UUID, str, int]) -> str:
        """Get storage key for entity ID"""
        return task_key(entity_id)
    
    def _get_user_tasks_key(self, user_id: Union[UUID, str]) -> str:
        """Get storage key for user's task list"""
        return task_user_tasks_key(user_id)

    def _serialize_entity(self, entity: GenerationTask) -> str:
        """Serialize task to JSON string"""
        data = self.mapper.to_dict(entity)
        return _json_dumps(data)
        
    def _deserialize_entity(self, data: str, entity_class: Type[GenerationTask] = None) -> GenerationTask:
        """Deserialize task from JSON string"""
        data_dict = _json_loads(data)
        return self.mapper.from_dict(data_dict)
    
    async def save(self, entity: GenerationTask) -> GenerationTask:
        """
        Save a task and update the user's task list.
        
        Args:
            entity: The task to save
            
        Returns:
            GenerationTask: The saved task
        """
        # Save the task
        saved_task = await super().save(entity)
        
        # Add to user's task list if user_id exists in input_data
        if entity.input_data and 'user_id' in entity.input_data:
            user_id = entity.input_data['user_id']
            user_tasks_key = self._get_user_tasks_key(user_id)
            await self.storage.sadd(user_tasks_key, str(entity.id))
            
        return saved_task
    
    async def get_by_user(
        self, 
        user_id: Union[UUID, str], 
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[GenerationTask]:
        """
        Get tasks for a specific user with optional filtering.
        
        Args:
            user_id: The user ID (can be UUID or string)
            status: Optional status filter
            task_type: Optional task type filter
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List[GenerationTask]: List of tasks
        """
        try:
            # Convert user_id to string if it's a UUID
            user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id
            
            # Get the user's task IDs
            user_tasks_key = self._get_user_tasks_key(user_id_str)
            task_ids = await self.storage.smembers(user_tasks_key)
            
            if not task_ids:
                return []
                
            # Get all tasks
            tasks = []
            for task_id in list(task_ids)[offset:offset + limit]:
                task = await self.get_by_id(task_id)
                if task:
                    tasks.append(task)
            
            # Apply filters
            if status is not None:
                tasks = [t for t in tasks if t.status == status]
                
            if task_type is not None:
                tasks = [t for t in tasks if t.task_type == task_type]
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting tasks for user {user_id}: {str(e)}")
            raise
    
    async def delete(self, entity_id: Union[UUID, str, int]) -> bool:
        """
        Delete a task and remove it from the user's task list.
        
        Args:
            entity_id: The ID of the task to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Get the task to get the user ID
        task = await self.get_by_id(entity_id)
        if not task:
            return False
            
        # Get user_id from input_data
        user_id = task.input_data.get("user_id") if task.input_data else None
        
        # Delete the task
        deleted = await super().delete(entity_id)
        
        # Remove from user's task list
        if deleted and user_id:
            user_tasks_key = self._get_user_tasks_key(user_id)
            await self.storage.srem(user_tasks_key, str(entity_id))
            
        return deleted
