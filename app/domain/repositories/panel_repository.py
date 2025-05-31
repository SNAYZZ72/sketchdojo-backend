# =============================================================================
# app/domain/repositories/panel_repository.py
# =============================================================================
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.panel import Panel

from .base import BaseRepository


class PanelRepository(BaseRepository[Panel]):
    """Repository interface for Panel entities."""

    @abstractmethod
    async def get_by_webtoon_id(self, webtoon_id: UUID) -> List[Panel]:
        """Get all panels for a specific webtoon."""
        pass

    @abstractmethod
    async def get_by_scene_id(self, scene_id: UUID) -> List[Panel]:
        """Get all panels for a specific scene."""
        pass

    @abstractmethod
    async def update_image(self, panel_id: UUID, image_url: str) -> None:
        """Update panel image URL."""
        pass

    @abstractmethod
    async def update_sequence(self, panel_id: UUID, sequence_number: int) -> None:
        """Update panel sequence number."""
        pass

    @abstractmethod
    async def get_max_sequence(self, webtoon_id: UUID) -> int:
        """Get the maximum sequence number for a webtoon."""
        pass

    @abstractmethod
    async def reorder_panels(self, panel_ids: List[UUID], sequence_start: int = 1) -> None:
        """Reorder multiple panels with consecutive sequence numbers."""
        pass
