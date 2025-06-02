# app/application/dto/task_dto.py
"""
Task Data Transfer Objects
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.generation_task import TaskStatus, TaskType


class TaskProgressDTO(BaseModel):
    """Task progress data transfer object"""

    current_step: int
    total_steps: int
    current_operation: str
    percentage: float


class TaskDTO(BaseModel):
    """Task data transfer object"""

    id: UUID
    task_type: TaskType
    status: TaskStatus
    progress: TaskProgressDTO
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
