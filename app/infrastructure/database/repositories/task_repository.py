# =============================================================================
# app/infrastructure/database/repositories/task_repository.py
# =============================================================================
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.task import Task, TaskPriority, TaskStatus, TaskType
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.task import TaskModel

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[Task]):
    """SQLAlchemy implementation of TaskRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: TaskModel) -> Task:
        """Convert database model to domain entity."""
        return Task(
            id=model.id,
            user_id=model.user_id,
            task_type=model.task_type,
            status=model.status,
            priority=model.priority,
            input_data=model.input_data or {},
            result_data=model.result_data,
            error_message=model.error_message,
            progress_percentage=model.progress_percentage,
            current_step=model.current_step,
            total_steps=model.total_steps,
            started_at=model.started_at,
            completed_at=model.completed_at,
            estimated_duration_seconds=model.estimated_duration_seconds,
            celery_task_id=model.celery_task_id,
            retry_count=model.retry_count,
            max_retries=model.max_retries,
        )

    def _to_model(self, entity: Task) -> TaskModel:
        """Convert domain entity to database model."""
        return TaskModel(
            id=entity.id,
            user_id=entity.user_id,
            task_type=entity.task_type,
            status=entity.status,
            priority=entity.priority,
            input_data=entity.input_data,
            result_data=entity.result_data,
            error_message=entity.error_message,
            progress_percentage=entity.progress_percentage,
            current_step=entity.current_step,
            total_steps=entity.total_steps,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            estimated_duration_seconds=entity.estimated_duration_seconds,
            celery_task_id=entity.celery_task_id,
            retry_count=entity.retry_count,
            max_retries=entity.max_retries,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, entity: Task) -> Task:
        """Create a new task."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        logger.info(f"Task created: {model.id}")
        return self._to_domain(model)

    async def get_by_id(self, entity_id: UUID) -> Optional[Task]:
        """Get task by ID."""
        result = await self.session.execute(select(TaskModel).where(TaskModel.id == entity_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_celery_id(self, celery_task_id: str) -> Optional[Task]:
        """Get task by Celery task ID."""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.celery_task_id == celery_task_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, entity: Task) -> Task:
        """Update an existing task."""
        await self.session.execute(
            update(TaskModel)
            .where(TaskModel.id == entity.id)
            .values(
                status=entity.status,
                priority=entity.priority,
                result_data=entity.result_data,
                error_message=entity.error_message,
                progress_percentage=entity.progress_percentage,
                current_step=entity.current_step,
                total_steps=entity.total_steps,
                started_at=entity.started_at,
                completed_at=entity.completed_at,
                estimated_duration_seconds=entity.estimated_duration_seconds,
                celery_task_id=entity.celery_task_id,
                retry_count=entity.retry_count,
                max_retries=entity.max_retries,
                updated_at=entity.updated_at,
            )
        )

        # Fetch updated model
        result = await self.session.execute(select(TaskModel).where(TaskModel.id == entity.id))
        model = result.scalar_one()

        logger.info(f"Task updated: {entity.id}")
        return self._to_domain(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a task by ID."""
        result = await self.session.execute(select(TaskModel).where(TaskModel.id == entity_id))
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            logger.info(f"Task deleted: {entity_id}")
            return True

        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Task]:
        """List all tasks with pagination."""
        result = await self.session.execute(
            select(TaskModel).limit(limit).offset(offset).order_by(TaskModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_user_tasks_paginated(
        self,
        user_id: UUID,
        page: int,
        size: int,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
    ) -> Tuple[List[Task], int]:
        """Get user's tasks with pagination and filtering."""
        # Build query filters
        filters = [TaskModel.user_id == user_id]
        if status:
            filters.append(TaskModel.status == status)
        if task_type:
            filters.append(TaskModel.task_type == task_type)

        # Get total count
        count_result = await self.session.execute(select(func.count(TaskModel.id)).where(*filters))
        total = count_result.scalar()

        # Get tasks
        offset = (page - 1) * size
        result = await self.session.execute(
            select(TaskModel)
            .where(*filters)
            .order_by(TaskModel.created_at.desc())
            .limit(size)
            .offset(offset)
        )
        models = result.scalars().all()
        tasks = [self._to_domain(model) for model in models]

        return tasks, total

    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """Get pending tasks for processing."""
        result = await self.session.execute(
            select(TaskModel)
            .where(TaskModel.status == TaskStatus.PENDING)
            .order_by(TaskModel.priority.desc(), TaskModel.created_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_running_tasks_by_user(self, user_id: UUID) -> List[Task]:
        """Get running tasks for a specific user."""
        result = await self.session.execute(
            select(TaskModel)
            .where(TaskModel.user_id == user_id, TaskModel.status == TaskStatus.RUNNING)
            .order_by(TaskModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]
