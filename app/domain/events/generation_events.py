# app/domain/events/generation_events.py
"""
Domain events for generation operations
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict
from uuid import UUID

from app.domain.entities.generation_task import TaskStatus


@dataclass
class DomainEvent:
    """Base domain event"""

    event_id: UUID
    timestamp: datetime
    aggregate_id: UUID
    event_type: str

    @classmethod
    def create(cls, aggregate_id: UUID, event_type: str, **kwargs):
        """Create a new domain event"""
        from uuid import uuid4

        return cls(
            event_id=uuid4(),
            timestamp=datetime.now(UTC),
            aggregate_id=aggregate_id,
            event_type=event_type,
            **kwargs
        )


@dataclass
class TaskCreatedEvent(DomainEvent):
    """Event fired when a generation task is created"""

    task_type: str
    input_data: Dict[str, Any]

    @classmethod
    def create(cls, task_id: UUID, task_type: str, input_data: Dict[str, Any]):
        return super().create(
            aggregate_id=task_id,
            event_type="task_created",
            task_type=task_type,
            input_data=input_data,
        )


@dataclass
class TaskStatusChangedEvent(DomainEvent):
    """Event fired when a task status changes"""

    old_status: TaskStatus
    new_status: TaskStatus
    progress_percentage: float

    @classmethod
    def create(
        cls,
        task_id: UUID,
        old_status: TaskStatus,
        new_status: TaskStatus,
        progress: float,
    ):
        return super().create(
            aggregate_id=task_id,
            event_type="task_status_changed",
            old_status=old_status,
            new_status=new_status,
            progress_percentage=progress,
        )


@dataclass
class PanelGeneratedEvent(DomainEvent):
    """Event fired when a panel is generated"""

    panel_id: UUID
    webtoon_id: UUID
    image_url: str

    @classmethod
    def create(cls, task_id: UUID, panel_id: UUID, webtoon_id: UUID, image_url: str):
        return super().create(
            aggregate_id=task_id,
            event_type="panel_generated",
            panel_id=panel_id,
            webtoon_id=webtoon_id,
            image_url=image_url,
        )


@dataclass
class WebtoonCompletedEvent(DomainEvent):
    """Event fired when a webtoon generation is completed"""

    webtoon_id: UUID
    panel_count: int

    @classmethod
    def create(cls, task_id: UUID, webtoon_id: UUID, panel_count: int):
        return super().create(
            aggregate_id=task_id,
            event_type="webtoon_completed",
            webtoon_id=webtoon_id,
            panel_count=panel_count,
        )
