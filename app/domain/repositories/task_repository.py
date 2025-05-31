# =============================================================================
# app/domain/repositories/task_repository.py
# =============================================================================
from abc import abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.models.task import Task

from .base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository interface for Task entities."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Task]:
        """Get all tasks assigned to a user."""
        pass

    @abstractmethod
    async def get_pending_by_user_id(self, user_id: UUID) -> List[Task]:
        """Get all pending tasks assigned to a user."""
        pass

    @abstractmethod
    async def update_status(self, task_id: UUID, status: str) -> None:
        """Update task status."""
        pass

    @abstractmethod
    async def update_progress(self, task_id: UUID, progress: float) -> None:
        """Update task progress percentage."""
        pass

    @abstractmethod
    async def set_completed(self, task_id: UUID, completed_at: datetime = None) -> None:
        """Mark task as completed."""
        pass

    @abstractmethod
    async def get_tasks_by_entity(self, entity_type: str, entity_id: UUID) -> List[Task]:
        """Get all tasks related to a specific entity (project, webtoon, etc.)."""
        pass
