# =============================================================================
# app/domain/repositories/webtoon_repository.py
# =============================================================================
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.webtoon import Webtoon

from .base import BaseRepository


class WebtoonRepository(BaseRepository[Webtoon]):
    """Repository interface for Webtoon entities."""

    @abstractmethod
    async def get_by_project_id(self, project_id: UUID) -> List[Webtoon]:
        """Get all webtoons by project ID."""
        pass

    @abstractmethod
    async def get_published(self) -> List[Webtoon]:
        """Get all published webtoons."""
        pass

    @abstractmethod
    async def update_status(self, webtoon_id: UUID, status: str) -> None:
        """Update webtoon status."""
        pass

    @abstractmethod
    async def update_thumbnail(self, webtoon_id: UUID, thumbnail_url: str) -> None:
        """Update webtoon thumbnail URL."""
        pass

    @abstractmethod
    async def increment_views(self, webtoon_id: UUID) -> None:
        """Increment the view count for a webtoon."""
        pass

    @abstractmethod
    async def increment_likes(self, webtoon_id: UUID) -> None:
        """Increment the like count for a webtoon."""
        pass
