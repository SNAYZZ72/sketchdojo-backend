# =============================================================================
# app/domain/models/task.py
# =============================================================================
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from .base import DomainEntity


class TaskType(str, Enum):
    STORY_GENERATION = "story_generation"
    SCENE_GENERATION = "scene_generation"
    PANEL_GENERATION = "panel_generation"
    IMAGE_GENERATION = "image_generation"
    WEBTOON_COMPILATION = "webtoon_compilation"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task(DomainEntity):
    """Task domain model for async processing."""

    user_id: UUID
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    # Task data
    input_data: Dict[str, Any] = field(default_factory=dict)
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Progress tracking
    progress_percentage: float = 0.0
    current_step: Optional[str] = None
    total_steps: int = 1

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[int] = None

    # Metadata
    celery_task_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def start(self, celery_task_id: str) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.celery_task_id = celery_task_id

    def update_progress(self, percentage: float, current_step: Optional[str] = None) -> None:
        """Update task progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        if current_step:
            self.current_step = current_step

    def complete(self, result_data: Dict[str, Any]) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result_data = result_data
        self.progress_percentage = 100.0

    def fail(self, error_message: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    def retry(self) -> None:
        """Prepare task for retry."""
        if self.can_retry():
            self.retry_count += 1
            self.status = TaskStatus.PENDING
            self.error_message = None
            self.started_at = None
            self.completed_at = None
            self.progress_percentage = 0.0
