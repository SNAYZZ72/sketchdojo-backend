# app/application/interfaces/storage_provider.py
"""
Storage provider interface for data persistence
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageProvider(ABC):
    """Interface for data storage providers"""

    @abstractmethod
    async def store(self, key: str, data: Any) -> bool:
        """Store data with a key"""

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data by key"""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete data by key"""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""

    @abstractmethod
    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching a pattern"""

    @abstractmethod
    async def store_json(self, key: str, data: Dict[str, Any]) -> bool:
        """Store JSON serializable data"""

    @abstractmethod
    async def retrieve_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data"""
