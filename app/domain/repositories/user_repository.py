# =============================================================================
# app/domain/repositories/user_repository.py
# =============================================================================
from abc import abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.models.user import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository interface for User entities."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        pass
