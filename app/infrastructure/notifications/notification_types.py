"""
Notification types and payload structure.
"""
from enum import Enum
from typing import Any, Dict, Optional, TypedDict, Union


class NotificationType(str, Enum):
    """Enum of notification types for inter-process communication."""
    
    # Webtoon related notifications
    WEBTOON_UPDATED = "sketchdojo:webtoon_updated"
    
    # Task related notifications
    TASK_PROGRESS = "sketchdojo:task_progress"
    TASK_COMPLETED = "sketchdojo:task_completed"
    TASK_FAILED = "sketchdojo:task_failed"


class TaskProgressPayload(TypedDict):
    """Payload for task progress notifications."""
    task_id: str
    progress: float
    message: str


class WebtoonUpdatedPayload(TypedDict):
    """Payload for webtoon updated notifications."""
    task_id: str
    webtoon_id: str
    html_content: str


class TaskCompletedPayload(TypedDict):
    """Payload for task completed notifications."""
    task_id: str
    result: Dict[str, Any]
    webtoon_id: Optional[str]


class TaskFailedPayload(TypedDict):
    """Payload for task failed notifications."""
    task_id: str
    error: str


# Union of all possible payload types
NotificationPayload = Union[
    TaskProgressPayload,
    WebtoonUpdatedPayload,
    TaskCompletedPayload,
    TaskFailedPayload,
]
