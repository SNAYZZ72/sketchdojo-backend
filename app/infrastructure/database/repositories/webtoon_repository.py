# =============================================================================
# app/infrastructure/database/repositories/webtoon_repository.py
# =============================================================================
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.webtoon import Webtoon, WebtoonStatus
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.webtoon import WebtoonModel

logger = logging.getLogger(__name__)


class WebtoonRepository(BaseRepository[Webtoon]):
    """SQLAlchemy implementation of WebtoonRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: WebtoonModel) -> Webtoon:
        """Convert database model to domain entity."""
        from app.domain.models.webtoon import WebtoonMetadata

        return Webtoon(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description,
            status=model.status,
            metadata=WebtoonMetadata(**model.metadata) if model.metadata else None,
            story_summary=model.story_summary,
            panel_count=model.panel_count,
            estimated_panels=model.estimated_panels,
            art_style_reference=model.art_style_reference,
            style_notes=model.style_notes,
            color_palette=model.color_palette or [],
            thumbnail_url=model.thumbnail_url,
            published_url=model.published_url,
            view_count=model.view_count,
            like_count=model.like_count,
        )

    def _to_model(self, entity: Webtoon) -> WebtoonModel:
        """Convert domain entity to database model."""
        return WebtoonModel(
            id=entity.id,
            project_id=entity.project_id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            metadata=entity.metadata.dict() if entity.metadata else {},
            story_summary=entity.story_summary,
            panel_count=entity.panel_count,
            estimated_panels=entity.estimated_panels,
            art_style_reference=entity.art_style_reference,
            style_notes=entity.style_notes,
            color_palette=entity.color_palette,
            thumbnail_url=entity.thumbnail_url,
            published_url=entity.published_url,
            view_count=entity.view_count,
            like_count=entity.like_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, entity: Webtoon) -> Webtoon:
        """Create a new webtoon."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        logger.info(f"Webtoon created: {model.id}")
        return self._to_domain(model)

    async def get_by_id(self, entity_id: UUID) -> Optional[Webtoon]:
        """Get webtoon by ID."""
        result = await self.session.execute(
            select(WebtoonModel).where(WebtoonModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_project_id(self, project_id: UUID) -> List[Webtoon]:
        """Get webtoons by project ID."""
        result = await self.session.execute(
            select(WebtoonModel)
            .where(WebtoonModel.project_id == project_id)
            .order_by(WebtoonModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, entity: Webtoon) -> Webtoon:
        """Update an existing webtoon."""
        await self.session.execute(
            update(WebtoonModel)
            .where(WebtoonModel.id == entity.id)
            .values(
                title=entity.title,
                description=entity.description,
                status=entity.status,
                metadata=entity.metadata.dict() if entity.metadata else {},
                story_summary=entity.story_summary,
                panel_count=entity.panel_count,
                estimated_panels=entity.estimated_panels,
                art_style_reference=entity.art_style_reference,
                style_notes=entity.style_notes,
                color_palette=entity.color_palette,
                thumbnail_url=entity.thumbnail_url,
                published_url=entity.published_url,
                view_count=entity.view_count,
                like_count=entity.like_count,
                updated_at=entity.updated_at,
            )
        )

        # Fetch updated model
        result = await self.session.execute(
            select(WebtoonModel).where(WebtoonModel.id == entity.id)
        )
        model = result.scalar_one()

        logger.info(f"Webtoon updated: {entity.id}")
        return self._to_domain(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a webtoon by ID."""
        result = await self.session.execute(
            select(WebtoonModel).where(WebtoonModel.id == entity_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            logger.info(f"Webtoon deleted: {entity_id}")
            return True

        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Webtoon]:
        """List all webtoons with pagination."""
        result = await self.session.execute(
            select(WebtoonModel)
            .limit(limit)
            .offset(offset)
            .order_by(WebtoonModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_published_webtoons(self, limit: int = 100, offset: int = 0) -> List[Webtoon]:
        """Get published webtoons."""
        result = await self.session.execute(
            select(WebtoonModel)
            .where(WebtoonModel.status == WebtoonStatus.PUBLISHED)
            .order_by(WebtoonModel.view_count.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]
