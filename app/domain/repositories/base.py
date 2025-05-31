"""
Repository Layer - Data Access Implementation
Files: app/infrastructure/database/repositories/
"""

# =============================================================================
# app/domain/repositories/base.py
# =============================================================================
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Tuple, TypeVar
from uuid import UUID

from app.domain.models.base import DomainEntity

T = TypeVar("T", bound=DomainEntity)


class BaseRepository(ABC, Generic[T]):
    """Base repository interface for all domain entities."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all entities with pagination."""
        pass
