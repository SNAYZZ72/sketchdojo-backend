# =============================================================================
# app/domain/models/project.py
# =============================================================================
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import DomainEntity


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Project(DomainEntity):
    """Project domain model."""

    user_id: UUID
    title: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Content structure
    story_outline: Optional[str] = None
    target_panels: int = 6
    art_style: str = "webtoon"  # webtoon, manga, comic
    color_palette: Optional[List[str]] = None

    def can_be_modified(self) -> bool:
        """Check if project can be modified."""
        return self.status in [ProjectStatus.DRAFT, ProjectStatus.IN_PROGRESS]

    def mark_in_progress(self) -> None:
        """Mark project as in progress."""
        if self.status == ProjectStatus.DRAFT:
            self.status = ProjectStatus.IN_PROGRESS

    def mark_completed(self) -> None:
        """Mark project as completed."""
        if self.status == ProjectStatus.IN_PROGRESS:
            self.status = ProjectStatus.COMPLETED
