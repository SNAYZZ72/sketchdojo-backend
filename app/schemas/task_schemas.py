# app/schemas/task_schemas.py
"""
Task-related API schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.application.dto.task_dto import TaskDTO, TaskProgressDTO
from app.domain.entities.generation_task import GenerationTask, TaskStatus, TaskType


class TaskProgressResponse(BaseModel):
    """Task progress response"""

    current_step: int
    total_steps: int
    current_operation: str
    percentage: float


class TaskResponse(BaseModel):
    """Task response schema"""

    id: UUID
    task_type: TaskType
    status: TaskStatus
    progress: TaskProgressResponse
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

    @classmethod
    def from_entity(cls, task: GenerationTask) -> "TaskResponse":
        return cls(
            id=task.id,
            task_type=task.task_type,
            status=task.status,
            progress=TaskProgressResponse(
                current_step=task.progress.current_step,
                total_steps=task.progress.total_steps,
                current_operation=task.progress.current_operation,
                percentage=task.progress.percentage,
            ),
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            result=task.result,
            execution_time=task.execution_time,
        )

    @classmethod
    def from_dto(cls, dto: TaskDTO) -> "TaskResponse":
        return cls(
            id=dto.id,
            task_type=dto.task_type,
            status=dto.status,
            progress=TaskProgressResponse(
                current_step=dto.progress.current_step,
                total_steps=dto.progress.total_steps,
                current_operation=dto.progress.current_operation,
                percentage=dto.progress.percentage,
            ),
            created_at=dto.created_at,
            started_at=dto.started_at,
            completed_at=dto.completed_at,
            error_message=dto.error_message,
            result=dto.result,
            execution_time=dto.execution_time,
        )


class TaskListResponse(BaseModel):
    """Response for task listing"""

    tasks: List[TaskResponse]
    total: int
