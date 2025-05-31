# =============================================================================
# app/schemas/task.py
# =============================================================================
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.task import TaskPriority, TaskStatus, TaskType

from .base import BaseEntitySchema, PaginatedResponse


class TaskCreate(BaseModel):
    """Schema for task creation."""

    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    input_data: Dict[str, Any]
    estimated_duration_seconds: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for task updates."""

    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    status: Optional[TaskStatus] = None


class TaskResponse(BaseEntitySchema):
    """Schema for task response."""

    user_id: UUID
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    progress_percentage: float
    current_step: Optional[str]
    total_steps: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_duration_seconds: Optional[int]
    celery_task_id: Optional[str]
    retry_count: int
    max_retries: int
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]


class TaskListResponse(BaseModel):
    """Schema for task list response."""

    id: UUID
    task_type: TaskType
    status: TaskStatus
    progress_percentage: float
    created_at: datetime
    estimated_duration_seconds: Optional[int]
