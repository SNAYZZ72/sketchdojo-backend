# =============================================================================
# app/domain/services/task_service.py
# =============================================================================
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.models.task import Task, TaskPriority, TaskStatus, TaskType
from app.domain.repositories.task_repository import TaskRepository
from app.schemas.task import TaskResponse

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task management."""

    def __init__(self, task_repository: TaskRepository):
        self.task_repo = task_repository

    async def create_task(
        self, user_id: UUID, task_type: str, input_data: dict, priority: str = "normal"
    ) -> Task:
        """Create a new task."""
        task = Task(
            user_id=user_id,
            task_type=TaskType(task_type),
            priority=TaskPriority(priority),
            input_data=input_data,
        )

        saved_task = await self.task_repo.create(task)

        logger.info(f"Task created: {saved_task.id} type={task_type} user={user_id}")
        return saved_task

    async def get_task(self, task_id: UUID, user_id: UUID) -> TaskResponse:
        """Get a task by ID."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")

        if task.user_id != user_id:
            raise PermissionError("Not authorized to access this task")

        return TaskResponse.from_orm(task)

    async def get_user_tasks_paginated(
        self,
        user_id: UUID,
        page: int,
        size: int,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
    ) -> Tuple[List[Task], int]:
        """Get user's tasks with pagination and filtering."""
        return await self.task_repo.get_user_tasks_paginated(user_id, page, size, status, task_type)

    async def start_task(self, task_id: UUID, celery_task_id: str):
        """Mark a task as started."""
        task = await self.task_repo.get_by_id(task_id)
        if task:
            task.start(celery_task_id)
            await self.task_repo.update(task)
            logger.info(f"Task started: {task_id} celery_id={celery_task_id}")

    async def update_task_progress(
        self, task_id: UUID, progress: float, current_step: Optional[str] = None
    ):
        """Update task progress."""
        task = await self.task_repo.get_by_id(task_id)
        if task:
            task.update_progress(progress, current_step)
            await self.task_repo.update(task)

    async def complete_task(self, task_id: UUID, result_data: dict):
        """Mark a task as completed."""
        task = await self.task_repo.get_by_id(task_id)
        if task:
            task.complete(result_data)
            await self.task_repo.update(task)
            logger.info(f"Task completed: {task_id}")

    async def fail_task(self, task_id: UUID, error_message: str):
        """Mark a task as failed."""
        task = await self.task_repo.get_by_id(task_id)
        if task:
            task.fail(error_message)
            await self.task_repo.update(task)
            logger.error(f"Task failed: {task_id} error={error_message}")

    async def cancel_task(self, task_id: UUID, user_id: UUID) -> TaskResponse:
        """Cancel a running task."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")

        if task.user_id != user_id:
            raise PermissionError("Not authorized to cancel this task")

        if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            raise ValueError("Task cannot be cancelled in its current status")

        # Cancel Celery task if it exists
        if task.celery_task_id:
            from app.core.celery_app import celery_app

            celery_app.control.revoke(task.celery_task_id, terminate=True)

        # Update task status
        task.status = TaskStatus.CANCELLED
        updated_task = await self.task_repo.update(task)

        logger.info(f"Task cancelled: {task_id}")
        return TaskResponse.from_orm(updated_task)

    async def retry_task(self, task_id: UUID, user_id: UUID) -> TaskResponse:
        """Retry a failed task."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")

        if task.user_id != user_id:
            raise PermissionError("Not authorized to retry this task")

        if not task.can_retry():
            raise ValueError("Task cannot be retried")

        # Reset task for retry
        task.retry()
        updated_task = await self.task_repo.update(task)

        # Requeue the task (implementation depends on task type)
        # This would typically involve calling the appropriate Celery task again

        logger.info(f"Task retry queued: {task_id} attempt={task.retry_count}")
        return TaskResponse.from_orm(updated_task)
