# app/infrastructure/storage/memory_storage.py
"""
In-memory storage implementation
"""
import fnmatch
import json
import logging
from typing import Any, Dict, List, Optional

from app.application.interfaces.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class MemoryStorage(StorageProvider):
    """In-memory storage implementation using dictionaries"""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        logger.info("Initialized in-memory storage")

    async def store(self, key: str, data: Any) -> bool:
        """Store data with a key"""
        try:
            self._data[key] = data
            logger.debug(f"Stored data for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing data for key {key}: {str(e)}")
            return False

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data by key"""
        try:
            return self._data.get(key)
        except Exception as e:
            logger.error(f"Error retrieving data for key {key}: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete data by key"""
        try:
            if key in self._data:
                del self._data[key]
                logger.debug(f"Deleted data for key: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting data for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return key in self._data

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching a pattern"""
        try:
            all_keys = list(self._data.keys())
            if pattern == "*":
                return all_keys
            return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            logger.error(f"Error listing keys with pattern {pattern}: {str(e)}")
            return []

    async def store_json(self, key: str, data: Dict[str, Any]) -> bool:
        """Store JSON serializable data"""
        try:
            # Serialize to ensure it's JSON serializable
            json_str = json.dumps(data)
            parsed_data = json.loads(json_str)  # Verify it's valid JSON
            return await self.store(key, parsed_data)
        except Exception as e:
            logger.error(f"Error storing JSON data for key {key}: {str(e)}")
            return False

    async def retrieve_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data"""
        try:
            data = await self.retrieve(key)
            if data is None:
                return None

            # Ensure it's a dictionary
            if isinstance(data, dict):
                return data

            # Try to parse if it's a string
            if isinstance(data, str):
                return json.loads(data)

            logger.warning(f"Data for key {key} is not JSON serializable")
            return None

        except Exception as e:
            logger.error(f"Error retrieving JSON data for key {key}: {str(e)}")
            return None

    def clear_all(self) -> None:
        """Clear all stored data (useful for testing)"""
        self._data.clear()
        logger.info("Cleared all stored data")

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "total_keys": len(self._data),
            "memory_usage_estimate": sum(
                len(str(k)) + len(str(v)) for k, v in self._data.items()
            ),
        }
