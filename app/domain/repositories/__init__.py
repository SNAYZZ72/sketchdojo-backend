# app/domain/repositories/__init__.py
"""
Repository interfaces for domain entities.
This module contains interfaces for data access and manipulation of domain entities.
"""

# app/domain/repositories/base_repository.py
"""
Base repository interface
"""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository interface for CRUD operations"""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save an entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """Get all entities"""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID"""
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists"""
        pass
