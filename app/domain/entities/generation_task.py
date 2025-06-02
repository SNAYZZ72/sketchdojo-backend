# app/domain/entities/generation_task.py
"""
Generation task domain entity
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Type of generation task"""

    WEBTOON_GENERATION = "webtoon_generation"
    PANEL_GENERATION = "panel_generation"
    IMAGE_GENERATION = "image_generation"
    STORY_GENERATION = "story_generation"


@dataclass
class TaskProgress:
    """Task progress tracking"""

    current_step: int = 0
    total_steps: int = 0
    current_operation: str = ""
    percentage: float = 0.0

    def update(self, step: int, operation: str) -> None:
        """Update progress"""
        self.current_step = step
        self.current_operation = operation
        if self.total_steps > 0:
            self.percentage = (step / self.total_steps) * 100


@dataclass
class GenerationTask:
    """
    Task entity for tracking generation operations
    """

    id: UUID = field(default_factory=uuid4)
    task_type: TaskType = TaskType.WEBTOON_GENERATION
    status: TaskStatus = TaskStatus.PENDING
    progress: TaskProgress = field(default_factory=TaskProgress)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now(UTC)

    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.result = result
        self.progress.percentage = 100.0

    def fail(self, error_message: str) -> None:
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.error_message = error_message

    def cancel(self) -> None:
        """Mark task as cancelled"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now(UTC)

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]

    @property
    def execution_time(self) -> Optional[float]:
        """Get task execution time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
