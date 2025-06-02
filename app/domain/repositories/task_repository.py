# app/domain/repositories/task_repository.py
"""
Task repository implementation using storage provider
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.generation_task import (
    GenerationTask,
    TaskProgress,
    TaskStatus,
    TaskType,
)
from app.domain.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[GenerationTask]):
    """Repository implementation for generation task entities"""

    def __init__(self, storage: StorageProvider):
        self.storage = storage
        self.key_prefix = "task:"
        logger.info("TaskRepository initialized")

    def _get_key(self, entity_id: UUID) -> str:
        """Get storage key for entity ID"""
        return f"{self.key_prefix}{str(entity_id)}"

    def _serialize_task(self, task: GenerationTask) -> dict:
        """Serialize task entity to dictionary"""
        return {
            "id": str(task.id),
            "task_type": task.task_type.value,
            "status": task.status.value,
            "progress": {
                "current_step": task.progress.current_step,
                "total_steps": task.progress.total_steps,
                "current_operation": task.progress.current_operation,
                "percentage": task.progress.percentage,
            },
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat()
            if task.completed_at
            else None,
            "error_message": task.error_message,
            "result": task.result,
            "input_data": task.input_data,
            "metadata": task.metadata,
        }

    def _deserialize_task(self, data: dict) -> GenerationTask:
        """Deserialize dictionary to task entity"""
        progress = TaskProgress(
            current_step=data["progress"]["current_step"],
            total_steps=data["progress"]["total_steps"],
            current_operation=data["progress"]["current_operation"],
            percentage=data["progress"]["percentage"],
        )

        task = GenerationTask(
            id=UUID(data["id"]),
            task_type=TaskType(data["task_type"]),
            status=TaskStatus(data["status"]),
            progress=progress,
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"])
            if data["started_at"]
            else None,
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data["completed_at"]
            else None,
            error_message=data["error_message"],
            result=data["result"],
            input_data=data.get("input_data", {}),
            metadata=data.get("metadata", {}),
        )

        return task

    async def save(self, entity: GenerationTask) -> GenerationTask:
        """Save a task entity"""
        try:
            key = self._get_key(entity.id)
            data = self._serialize_task(entity)

            success = await self.storage.store_json(key, data)
            if not success:
                raise RuntimeError(f"Failed to save task {entity.id}")

            logger.debug(f"Saved task: {entity.id}")
            return entity

        except Exception as e:
            logger.error(f"Error saving task {entity.id}: {str(e)}")
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[GenerationTask]:
        """Get task by ID"""
        try:
            key = self._get_key(entity_id)
            data = await self.storage.retrieve_json(key)

            if data is None:
                return None

            return self._deserialize_task(data)

        except Exception as e:
            logger.error(f"Error retrieving task {entity_id}: {str(e)}")
            return None

    async def get_all(self) -> List[GenerationTask]:
        """Get all tasks"""
        try:
            keys = await self.storage.list_keys(f"{self.key_prefix}*")
            tasks = []

            for key in keys:
                data = await self.storage.retrieve_json(key)
                if data:
                    task = self._deserialize_task(data)
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
        tasks = await self.get_all()
        return [t for t in tasks if t.status == status]

    async def get_by_type(self, task_type: TaskType) -> List[GenerationTask]:
        """Get tasks by type"""
        tasks = await self.get_all()
        return [t for t in tasks if t.task_type == task_type]

    async def get_active_tasks(self) -> List[GenerationTask]:
        """Get all non-terminal tasks"""
        tasks = await self.get_all()
        return [t for t in tasks if not t.is_terminal]

    async def get_user_tasks(self, user_id: str) -> List[GenerationTask]:
        """Get tasks for a specific user (placeholder implementation)"""
        # In a real implementation, this would filter by user ID
        return await self.get_all()

    async def create(self, entity: GenerationTask) -> GenerationTask:
        """Create a new entity"""
        return await self.save(entity)

    async def update(
        self, entity_id: UUID, data: Dict[str, Any]
    ) -> Optional[GenerationTask]:
        """Update an entity"""
        try:
            existing_task = await self.get_by_id(entity_id)
            if not existing_task:
                return None

            # Update task fields from data dictionary
            for key, value in data.items():
                if hasattr(existing_task, key):
                    setattr(existing_task, key, value)

            # Save the updated task
            return await self.save(existing_task)

        except Exception as e:
            logger.error(f"Error updating task {entity_id}: {str(e)}")
            return None
