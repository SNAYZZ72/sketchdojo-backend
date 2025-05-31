# =============================================================================
# app/domain/models/webtoon.py
# =============================================================================
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import DomainEntity


class WebtoonStatus(str, Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WebtoonGenre(str, Enum):
    ACTION = "action"
    ROMANCE = "romance"
    COMEDY = "comedy"
    DRAMA = "drama"
    FANTASY = "fantasy"
    HORROR = "horror"
    SLICE_OF_LIFE = "slice_of_life"
    MYSTERY = "mystery"
    SCI_FI = "sci_fi"


@dataclass
class WebtoonMetadata:
    """Webtoon metadata and settings."""

    genre: WebtoonGenre
    target_audience: str  # "children", "teen", "young_adult", "adult"
    content_rating: str  # "G", "PG", "PG-13", "R"
    tags: List[str] = field(default_factory=list)
    color_scheme: str = "full_color"  # "full_color", "limited_color", "monochrome"
    aspect_ratio: str = "vertical"  # "vertical", "square", "horizontal"


@dataclass
class Webtoon(DomainEntity):
    """Webtoon domain model."""

    project_id: UUID
    title: str
    description: str
    status: WebtoonStatus = WebtoonStatus.PLANNING
    metadata: WebtoonMetadata = field(
        default_factory=lambda: WebtoonMetadata(
            genre=WebtoonGenre.SLICE_OF_LIFE, target_audience="teen", content_rating="PG"
        )
    )

    # Content structure
    story_summary: Optional[str] = None
    panel_count: int = 0
    estimated_panels: int = 6

    # Visual consistency
    art_style_reference: Optional[str] = None
    style_notes: Optional[str] = None
    color_palette: List[str] = field(default_factory=list)

    # Publication
    thumbnail_url: Optional[str] = None
    published_url: Optional[str] = None
    view_count: int = 0
    like_count: int = 0

    def can_be_published(self) -> bool:
        """Check if webtoon can be published."""
        return (
            self.status == WebtoonStatus.COMPLETED
            and self.panel_count > 0
            and self.thumbnail_url is not None
        )

    def mark_in_progress(self) -> None:
        """Mark webtoon as in progress."""
        if self.status == WebtoonStatus.PLANNING:
            self.status = WebtoonStatus.IN_PROGRESS

    def mark_completed(self) -> None:
        """Mark webtoon as completed."""
        if self.status == WebtoonStatus.IN_PROGRESS:
            self.status = WebtoonStatus.COMPLETED

    def publish(self, published_url: str) -> None:
        """Publish the webtoon."""
        if self.can_be_published():
            self.status = WebtoonStatus.PUBLISHED
            self.published_url = published_url
