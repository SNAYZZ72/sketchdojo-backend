# =============================================================================
# app/domain/repositories/project_repository.py
# =============================================================================
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.project import Project

from .base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository interface for Project entities."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Project]:
        """Get all projects by user ID."""
        pass

    @abstractmethod
    async def get_active_by_user_id(self, user_id: UUID) -> List[Project]:
        """Get all active projects by user ID."""
        pass

    @abstractmethod
    async def update_status(self, project_id: UUID, status: str) -> None:
        """Update project status."""
        pass

    @abstractmethod
    async def update_thumbnail(self, project_id: UUID, thumbnail_url: str) -> None:
        """Update project thumbnail URL."""
        pass
