# app/infrastructure/storage/file_storage.py
"""
File system storage implementation
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from app.application.interfaces.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


class FileStorage(StorageProvider):
    """File system storage implementation"""

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized file storage at: {self.base_path}")

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key"""
        # Replace colons and other invalid characters
        safe_key = key.replace(":", "_").replace("/", "_")
        return self.base_path / f"{safe_key}.json"

    async def store(self, key: str, data: Any) -> bool:
        """Store data to file"""
        try:
            file_path = self._get_file_path(key)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "w") as f:
                if isinstance(data, (dict, list)):
                    await f.write(json.dumps(data, default=str))
                else:
                    await f.write(str(data))

            logger.debug(f"Stored data to file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error storing data for key {key}: {str(e)}")
            return False

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from file"""
        try:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content

        except Exception as e:
            logger.error(f"Error retrieving data for key {key}: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete data file"""
        try:
            file_path = self._get_file_path(key)

            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting data for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if file exists"""
        file_path = self._get_file_path(key)
        return file_path.exists()

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern"""
        try:
            keys = []
            # Convert pattern to a safe file pattern
            # Replace ':' with '_' for file system safety
            safe_pattern = pattern.replace(":", "_")

            # Log the raw pattern and all files in the directory for debugging
            logger.info(f"Raw pattern provided: '{pattern}'")
            all_files = list(self.base_path.glob("*.json"))
            logger.info(f"All JSON files in storage directory: {len(all_files)} files")
            for file in all_files:
                logger.info(f"Found file: {file.name}")

            # If pattern ends with *, adjust it for glob
            if safe_pattern.endswith("*"):
                file_pattern = f"{safe_pattern[:-1]}*.json"
            else:
                file_pattern = f"{safe_pattern}.json"

            logger.info(f"Searching with pattern: '{file_pattern}'")

            # Use the converted pattern to find matching files
            matching_files = list(self.base_path.glob(file_pattern))
            logger.info(f"Glob found {len(matching_files)} files matching pattern")

            for file_path in matching_files:
                # Convert back from safe filename to key format
                key = file_path.stem.replace("_", ":")
                logger.info(f"Converting filename {file_path.stem} to key {key}")
                keys.append(key)

            logger.info(f"Returning {len(keys)} keys matching pattern '{pattern}'")
            return keys

        except Exception as e:
            logger.error(f"Error listing keys: {str(e)}")
            logger.exception("Full stack trace:")
            return []

    async def store_json(self, key: str, data: Dict[str, Any]) -> bool:
        """Store JSON data"""
        return await self.store(key, data)
    
    def store_sync(self, key: str, data: Any) -> bool:
        """Synchronous version of store method for use in Celery tasks"""
        try:
            file_path = self._get_file_path(key)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w") as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, default=str)
                else:
                    f.write(str(data))
            
            logger.debug(f"Synchronously stored data to file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error synchronously storing data for key {key}: {str(e)}")
            return False
    
    def retrieve_sync(self, key: str) -> Optional[Any]:
        """Synchronous version of retrieve method for use in Celery tasks"""
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
                
            with open(file_path, "r") as f:
                content = f.read()
                
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
                
        except Exception as e:
            logger.error(f"Error synchronously retrieving data for key {key}: {str(e)}")
            return None

    async def retrieve_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data"""
        data = await self.retrieve(key)
        if isinstance(data, dict):
            return data
        return None
        
    def store_json_sync(self, key: str, data: Dict[str, Any]) -> bool:
        """Synchronous version of store_json method for use in Celery tasks"""
        return self.store_sync(key, data)
        
    def retrieve_json_sync(self, key: str) -> Optional[Dict[str, Any]]:
        """Synchronous version of retrieve_json method for use in Celery tasks"""
        data = self.retrieve_sync(key)
        if isinstance(data, dict):
            return data
        return None
