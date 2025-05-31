# =============================================================================
# app/domain/repositories/character_repository.py
# =============================================================================
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.character import Character

from .base import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    """Repository interface for Character entities."""

    @abstractmethod
    async def get_by_project_id(self, project_id: UUID) -> List[Character]:
        """Get all characters for a specific project."""
        pass

    @abstractmethod
    async def update_image(self, character_id: UUID, image_url: str) -> None:
        """Update character image URL."""
        pass

    @abstractmethod
    async def get_by_name(self, project_id: UUID, name: str) -> Optional[Character]:
        """Get a character by name within a project."""
        pass

    @abstractmethod
    async def get_featured(self, limit: int = 10) -> List[Character]:
        """Get featured characters."""
        pass
