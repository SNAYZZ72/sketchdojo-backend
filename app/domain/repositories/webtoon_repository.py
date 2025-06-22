# app/domain/repositories/webtoon_repository.py
"""
Webtoon repository implementation using storage provider
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.storage_provider import StorageProvider
from app.domain.entities.webtoon import Webtoon
from app.domain.mappers.webtoon_mapper import WebtoonDataMapper
from app.domain.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class WebtoonRepository(BaseRepository[Webtoon]):
    """Repository implementation for webtoon entities"""

    def __init__(self, storage: StorageProvider, mapper: WebtoonDataMapper = None):
        self.storage = storage
        self.key_prefix = "webtoon:"
        self.mapper = mapper or WebtoonDataMapper()
        logger.info("WebtoonRepository initialized")

    def _get_key(self, entity_id: UUID) -> str:
        """Get storage key for entity ID"""
        return f"{self.key_prefix}{str(entity_id)}"

    async def save(self, entity: Webtoon) -> Webtoon:
        """Save a webtoon entity (create or update)"""
        try:
            key = self._get_key(entity.id)
            data = self.mapper.to_dict(entity)
            success = await self.storage.store(key, data)
            if not success:
                raise RuntimeError(f"Failed to save webtoon {entity.id}")
            logger.debug(f"Saved webtoon: {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error saving webtoon {entity.id}: {str(e)}")
            raise

    def save_sync(self, entity: Webtoon) -> Webtoon:
        """Save a webtoon entity synchronously (for Celery tasks)"""
        try:
            key = self._get_key(entity.id)
            data = self.mapper.to_dict(entity)
            
            # Check if the storage provider has sync methods
            if hasattr(self.storage, 'store_sync'):
                success = self.storage.store_sync(key, data)
            else:
                # Fallback to regular store for non-async providers
                success = self.storage.store(key, data)
                
            if not success:
                raise RuntimeError(f"Failed to save webtoon {entity.id}")
            logger.debug(f"Saved webtoon: {entity.id} synchronously")
            return entity
        except Exception as e:
            logger.error(f"Error saving webtoon {entity.id} synchronously: {str(e)}")
            raise

    async def get_by_id(self, entity_id: UUID) -> Optional[Webtoon]:
        """Get webtoon by ID"""
        try:
            key = self._get_key(entity_id)
            data = await self.storage.retrieve(key)
            if data is None:
                return None
            return self.mapper.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving webtoon {entity_id}: {str(e)}")
            return None
            
    def get_by_id_sync(self, entity_id: UUID) -> Optional[Webtoon]:
        """Get webtoon by ID synchronously (for Celery tasks)"""
        try:
            key = self._get_key(entity_id)
            
            # Check if the storage provider has sync methods
            if hasattr(self.storage, 'retrieve_sync'):
                data = self.storage.retrieve_sync(key)
            else:
                # Fallback to regular retrieve for non-async providers
                data = self.storage.retrieve(key)
                
            if data is None:
                return None
            return self.mapper.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving webtoon {entity_id} synchronously: {str(e)}")
            return None

    async def update_fields(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[Webtoon]:
        """Update specific fields of a webtoon entity"""
        webtoon = await self.get_by_id(entity_id)
        if not webtoon:
            return None
            
        # Update fields from data dictionary
        for key, value in data.items():
            if hasattr(webtoon, key):
                setattr(webtoon, key, value)
        
        # Save the updated webtoon
        return await self.save(webtoon)

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Webtoon]:
        """Get all webtoons with optional pagination and filtering"""
        try:
            keys = await self.storage.list_keys(f"{self.key_prefix}*")
            webtoons = []
            for key in keys[skip:skip+limit]:
                data = await self.storage.retrieve(key)
                if data is not None:
                    webtoon = self.mapper.from_dict(data)
                    
                    # Apply filters if any
                    if filters:
                        include = True
                        for field, value in filters.items():
                            if hasattr(webtoon, field) and getattr(webtoon, field) != value:
                                include = False
                                break
                        if not include:
                            continue
                            
                    webtoons.append(webtoon)
            return webtoons
        except Exception as e:
            logger.error(f"Error retrieving all webtoons: {str(e)}")
            return []

    async def delete(self, entity_id: UUID) -> bool:
        """Delete webtoon by ID"""
        try:
            key = self._get_key(entity_id)
            return await self.storage.delete(key)
        except Exception as e:
            logger.error(f"Error deleting webtoon {entity_id}: {str(e)}")
            return False

    async def exists(self, entity_id: UUID) -> bool:
        """Check if webtoon exists"""
        try:
            key = self._get_key(entity_id)
            return await self.storage.exists(key)
        except Exception as e:
            logger.error(f"Error checking webtoon existence {entity_id}: {str(e)}")
            return False

    async def get_by_title(self, title: str) -> Optional[Webtoon]:
        """Get webtoon by title"""
        webtoons = await self.get_all()
        return next((w for w in webtoons if w.title == title), None)

    async def get_published(self) -> List[Webtoon]:
        """Get all published webtoons"""
        return await self.get_all(is_published=True)

    async def search_by_keyword(self, keyword: str) -> List[Webtoon]:
        """Search webtoons by keyword in title or description"""
        webtoons = await self.get_all()
        keyword_lower = keyword.lower()
        return [
            w
            for w in webtoons
            if keyword_lower in w.title.lower()
            or keyword_lower in w.description.lower()
        ]
