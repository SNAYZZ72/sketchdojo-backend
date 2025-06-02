# app/domain/repositories/base_repository.py
"""
Base repository for data access operations
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

T = TypeVar("T")  # Generic type for entity


class BaseRepository(Generic[T], ABC):
    """Abstract base repository for CRUD operations"""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all entities with optional pagination and filtering"""
        pass

    @abstractmethod
    async def update(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """Update an entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete an entity"""
        pass
