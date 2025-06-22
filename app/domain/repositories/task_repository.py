# app/domain/repositories/task_repository.py
"""
Task repository implementation using storage provider
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.generation_task import GenerationTask, TaskStatus, TaskType
from app.domain.mappers.task_mapper import TaskDataMapper
from app.domain.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[GenerationTask]):
    """Repository implementation for generation task entities"""

    def __init__(self, storage: StorageProvider, mapper: TaskDataMapper = None):
        self.storage = storage
        self.key_prefix = "task:"
        self.mapper = mapper or TaskDataMapper()
        logger.info("TaskRepository initialized")

    def _get_key(self, entity_id: UUID) -> str:
        """Get storage key for entity ID"""
        return f"{self.key_prefix}{str(entity_id)}"

    async def save(self, entity: GenerationTask) -> GenerationTask:
        """Save a task entity (create or update)"""
        try:
            key = self._get_key(entity.id)
            data = self.mapper.to_dict(entity)
            success = await self.storage.store(key, data)
            if not success:
                raise RuntimeError(f"Failed to save task {entity.id}")
            logger.debug(f"Saved task: {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error saving task {entity.id}: {str(e)}")
            raise
            
    def save_sync(self, entity: GenerationTask) -> GenerationTask:
        """Save a task entity synchronously (for Celery tasks)"""
        try:
            key = self._get_key(entity.id)
            data = self.mapper.to_dict(entity)
            
            # Check if the storage provider has sync methods
            if hasattr(self.storage, 'store_sync'):
                success = self.storage.store_sync(key, data)
            else:
                # Fallback to regular store for non-async providers
                success = self.storage.store(key, data)
                
            if not success:
                raise RuntimeError(f"Failed to save task {entity.id}")
            logger.debug(f"Saved task: {entity.id} synchronously")
            return entity
        except Exception as e:
            logger.error(f"Error saving task {entity.id} synchronously: {str(e)}")
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[GenerationTask]:
        """Get task by ID"""
        try:
            key = self._get_key(entity_id)
            data = await self.storage.retrieve(key)
            if data is None:
                return None
            return self.mapper.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving task {entity_id}: {str(e)}")
            return None
            
    def get_by_id_sync(self, entity_id: UUID) -> Optional[GenerationTask]:
        """Get task by ID synchronously (for Celery tasks)"""
        try:
            key = self._get_key(entity_id)
            
            # Check if the storage provider has sync methods
            if hasattr(self.storage, 'retrieve_sync'):
                data = self.storage.retrieve_sync(key)
            else:
                # Fallback to regular retrieve for non-async providers
                data = self.storage.retrieve(key)
                
            if data is None:
                return None
            return self.mapper.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving task {entity_id} synchronously: {str(e)}")
            return None

    async def update_fields(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[GenerationTask]:
        """Update specific fields of a task entity"""
        task = await self.get_by_id(entity_id)
        if not task:
            return None
            
        # Update fields from data dictionary
        for key, value in data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # Save the updated task
        return await self.save(task)

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[GenerationTask]:
        """Get all tasks with optional pagination and filtering"""
        try:
            keys = await self.storage.list_keys(f"{self.key_prefix}*")
            tasks = []
            for key in keys[skip:skip+limit]:
                data = await self.storage.retrieve(key)
                if data is not None:
                    task = self.mapper.from_dict(data)
                    
                    # Apply filters if any
                    if filters:
                        include = True
                        for field, value in filters.items():
                            if hasattr(task, field) and getattr(task, field) != value:
                                include = False
                                break
                        if not include:
                            continue
                            
                    tasks.append(task)
            return tasks
        except Exception as e:
            logger.error(f"Error retrieving all tasks: {str(e)}")
            return []

    async def delete(self, entity_id: UUID) -> bool:
        """Delete task by ID"""
        try:
            key = self._get_key(entity_id)
            return await self.storage.delete(key)
        except Exception as e:
            logger.error(f"Error deleting task {entity_id}: {str(e)}")
            return False

    async def exists(self, entity_id: UUID) -> bool:
        """Check if task exists"""
        try:
            key = self._get_key(entity_id)
            return await self.storage.exists(key)
        except Exception as e:
            logger.error(f"Error checking task existence {entity_id}: {str(e)}")
            return False

    async def get_by_status(self, status: TaskStatus) -> List[GenerationTask]:
        """Get tasks by status"""
        return await self.get_all(status=status)

    async def get_by_type(self, task_type: TaskType) -> List[GenerationTask]:
        """Get tasks by type"""
        return await self.get_all(task_type=task_type)

    async def get_active_tasks(self) -> List[GenerationTask]:
        """Get all non-terminal tasks"""
        tasks = await self.get_all()
        return [t for t in tasks if not t.is_terminal]

    async def get_user_tasks(self, user_id: str) -> List[GenerationTask]:
        """Get tasks for a specific user"""
        tasks = await self.get_all()
        return [t for t in tasks if t.metadata.get("user_id") == user_id]

    # BaseRepository compatibility methods - use save instead
    async def create(self, entity: GenerationTask) -> GenerationTask:
        """Create a new entity - delegates to save"""
        return await self.save(entity)

    async def update(self, entity_id: UUID, entity: GenerationTask) -> Optional[GenerationTask]:
        """Update an entity - delegates to save"""
        if not await self.exists(entity_id) or str(entity_id) != str(entity.id):
            return None
        return await self.save(entity)
