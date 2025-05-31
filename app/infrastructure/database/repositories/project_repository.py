# =============================================================================
# app/infrastructure/database/repositories/project_repository.py
# =============================================================================
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.project import Project, ProjectStatus
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.project import ProjectModel

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository[Project]):
    """SQLAlchemy implementation of ProjectRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: ProjectModel) -> Project:
        """Convert database model to domain entity."""
        return Project(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            description=model.description,
            status=model.status,
            thumbnail_url=model.thumbnail_url,
            metadata=model.metadata or {},
            story_outline=model.story_outline,
            target_panels=model.target_panels,
            art_style=model.art_style,
            color_palette=model.color_palette or [],
        )

    def _to_model(self, entity: Project) -> ProjectModel:
        """Convert domain entity to database model."""
        return ProjectModel(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            thumbnail_url=entity.thumbnail_url,
            metadata=entity.metadata,
            story_outline=entity.story_outline,
            target_panels=entity.target_panels,
            art_style=entity.art_style,
            color_palette=entity.color_palette,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, entity: Project) -> Project:
        """Create a new project."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        logger.info(f"Project created: {model.id}")
        return self._to_domain(model)

    async def get_by_id(self, entity_id: UUID) -> Optional[Project]:
        """Get project by ID."""
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, entity: Project) -> Project:
        """Update an existing project."""
        await self.session.execute(
            update(ProjectModel)
            .where(ProjectModel.id == entity.id)
            .values(
                title=entity.title,
                description=entity.description,
                status=entity.status,
                thumbnail_url=entity.thumbnail_url,
                metadata=entity.metadata,
                story_outline=entity.story_outline,
                target_panels=entity.target_panels,
                art_style=entity.art_style,
                color_palette=entity.color_palette,
                updated_at=entity.updated_at,
            )
        )

        # Fetch updated model
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.id == entity.id)
        )
        model = result.scalar_one()

        logger.info(f"Project updated: {entity.id}")
        return self._to_domain(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a project by ID."""
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.id == entity_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            logger.info(f"Project deleted: {entity_id}")
            return True

        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Project]:
        """List all projects with pagination."""
        result = await self.session.execute(
            select(ProjectModel)
            .limit(limit)
            .offset(offset)
            .order_by(ProjectModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_user_projects(self, user_id: UUID) -> List[Project]:
        """Get all projects for a user."""
        result = await self.session.execute(
            select(ProjectModel)
            .where(ProjectModel.user_id == user_id)
            .order_by(ProjectModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_user_projects_paginated(
        self, user_id: UUID, page: int, size: int
    ) -> Tuple[List[Project], int]:
        """Get user's projects with pagination."""
        # Get total count
        count_result = await self.session.execute(
            select(func.count(ProjectModel.id)).where(ProjectModel.user_id == user_id)
        )
        total = count_result.scalar()

        # Get projects
        offset = (page - 1) * size
        result = await self.session.execute(
            select(ProjectModel)
            .where(ProjectModel.user_id == user_id)
            .order_by(ProjectModel.created_at.desc())
            .limit(size)
            .offset(offset)
        )
        models = result.scalars().all()
        projects = [self._to_domain(model) for model in models]

        return projects, total
