# =============================================================================
# app/infrastructure/database/models/task.py
# =============================================================================
from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.models.task import TaskPriority, TaskStatus, TaskType

from .base import BaseModel


class TaskModel(BaseModel):
    """Task database model."""

    __tablename__ = "tasks"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL, nullable=False)

    # Task data stored as JSON
    input_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    current_step = Column(String(200), nullable=True)
    total_steps = Column(Integer, default=1, nullable=False)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration_seconds = Column(Integer, nullable=True)

    # Metadata
    celery_task_id = Column(String(100), nullable=True, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="tasks")
