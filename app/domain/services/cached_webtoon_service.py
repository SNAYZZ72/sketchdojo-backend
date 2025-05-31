# =============================================================================
# Example usage in service layer with caching
# =============================================================================
# app/domain/services/cached_webtoon_service.py

import logging
from typing import List, Optional
from uuid import UUID

from app.domain.services.webtoon_service import WebtoonService
from app.infrastructure.cache import cache_service
from app.schemas.project import ProjectResponse
from app.schemas.webtoon import WebtoonResponse

logger = logging.getLogger(__name__)


class CachedWebtoonService(WebtoonService):
    """WebtoonService with caching layer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = cache_service

    @cache_service.cached(ttl=3600, key_template="project:{0}")
    async def get_project(self, project_id: UUID, user_id: UUID) -> ProjectResponse:
        """Get project with caching."""
        return await super().get_project(project_id, user_id)

    @cache_service.cached(ttl=1800, key_template="webtoon:{0}")
    async def get_webtoon(self, webtoon_id: UUID, user_id: UUID) -> WebtoonResponse:
        """Get webtoon with caching."""
        return await super().get_webtoon(webtoon_id, user_id)

    @cache_service.cache_invalidate(pattern="user:{1}:*")
    async def create_project(self, user_id: UUID, project_data) -> ProjectResponse:
        """Create project and invalidate user cache."""
        return await super().create_project(user_id, project_data)

    @cache_service.cache_invalidate(pattern="project:{0}:*")
    async def update_project(
        self, project_id: UUID, user_id: UUID, project_data
    ) -> ProjectResponse:
        """Update project and invalidate project cache."""
        result = await super().update_project(project_id, user_id, project_data)

        # Also invalidate user cache
        await self.cache.clear_user_cache(str(user_id), "projects")

        return result

    async def get_user_projects_cached(self, user_id: UUID) -> List[ProjectResponse]:
        """Get user projects with caching."""
        cache_key = f"user_projects:{user_id}"

        cached_projects = await self.cache.get_user_cache(str(user_id), "projects", "list")

        if cached_projects is not None:
            return cached_projects

        # Fetch from database
        projects, _ = await self.project_repo.get_user_projects_paginated(user_id, 1, 100)

        project_responses = [ProjectResponse.model_validate(p) for p in projects]

        # Cache for 30 minutes
        await self.cache.set_user_cache(
            str(user_id), "projects", "list", project_responses, ttl=1800
        )

        return project_responses
