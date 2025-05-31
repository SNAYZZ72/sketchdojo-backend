# =============================================================================
# app/infrastructure/database/repositories/panel_repository.py
# =============================================================================
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.panel import Panel, PanelLayout, PanelSize, PanelStatus
from app.domain.repositories.base import BaseRepository
from app.infrastructure.database.models.panel import PanelModel

logger = logging.getLogger(__name__)


class PanelRepository(BaseRepository[Panel]):
    """SQLAlchemy implementation of PanelRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: PanelModel) -> Panel:
        """Convert database model to domain entity."""
        from app.domain.models.panel import SpeechBubble, VisualElement

        # Convert speech bubbles
        speech_bubbles = []
        if model.speech_bubbles:
            for bubble_data in model.speech_bubbles:
                speech_bubbles.append(SpeechBubble(**bubble_data))

        # Convert visual elements
        visual_elements = []
        if model.visual_elements:
            for element_data in model.visual_elements:
                visual_elements.append(VisualElement(**element_data))

        return Panel(
            id=model.id,
            webtoon_id=model.webtoon_id,
            scene_id=model.scene_id,
            sequence_number=model.sequence_number,
            size=model.size,
            layout=model.layout,
            status=model.status,
            visual_description=model.visual_description,
            characters_present=model.characters_present or [],
            speech_bubbles=speech_bubbles,
            visual_elements=visual_elements,
            ai_prompt=model.ai_prompt,
            image_url=model.image_url,
            generation_metadata=model.generation_metadata or {},
            feedback=model.feedback,
            revision_notes=model.revision_notes,
        )

    def _to_model(self, entity: Panel) -> PanelModel:
        """Convert domain entity to database model."""
        # Convert speech bubbles to dicts
        speech_bubbles_data = []
        for bubble in entity.speech_bubbles:
            if hasattr(bubble, "dict"):
                speech_bubbles_data.append(bubble.dict())
            else:
                speech_bubbles_data.append(bubble)

        # Convert visual elements to dicts
        visual_elements_data = []
        for element in entity.visual_elements:
            if hasattr(element, "dict"):
                visual_elements_data.append(element.dict())
            else:
                visual_elements_data.append(element)

        return PanelModel(
            id=entity.id,
            webtoon_id=entity.webtoon_id,
            scene_id=entity.scene_id,
            sequence_number=entity.sequence_number,
            size=entity.size,
            layout=entity.layout,
            status=entity.status,
            visual_description=entity.visual_description,
            characters_present=entity.characters_present,
            speech_bubbles=speech_bubbles_data,
            visual_elements=visual_elements_data,
            ai_prompt=entity.ai_prompt,
            image_url=entity.image_url,
            generation_metadata=entity.generation_metadata,
            feedback=entity.feedback,
            revision_notes=entity.revision_notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, entity: Panel) -> Panel:
        """Create a new panel."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        logger.info(f"Panel created: {model.id}")
        return self._to_domain(model)

    async def get_by_id(self, entity_id: UUID) -> Optional[Panel]:
        """Get panel by ID."""
        result = await self.session.execute(select(PanelModel).where(PanelModel.id == entity_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_webtoon_id(self, webtoon_id: UUID) -> List[Panel]:
        """Get panels by webtoon ID."""
        result = await self.session.execute(
            select(PanelModel)
            .where(PanelModel.webtoon_id == webtoon_id)
            .order_by(PanelModel.sequence_number.asc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, entity: Panel) -> Panel:
        """Update an existing panel."""
        # Convert speech bubbles and visual elements
        speech_bubbles_data = []
        for bubble in entity.speech_bubbles:
            if hasattr(bubble, "dict"):
                speech_bubbles_data.append(bubble.dict())
            else:
                speech_bubbles_data.append(bubble)

        visual_elements_data = []
        for element in entity.visual_elements:
            if hasattr(element, "dict"):
                visual_elements_data.append(element.dict())
            else:
                visual_elements_data.append(element)

        await self.session.execute(
            update(PanelModel)
            .where(PanelModel.id == entity.id)
            .values(
                sequence_number=entity.sequence_number,
                size=entity.size,
                layout=entity.layout,
                status=entity.status,
                visual_description=entity.visual_description,
                characters_present=entity.characters_present,
                speech_bubbles=speech_bubbles_data,
                visual_elements=visual_elements_data,
                ai_prompt=entity.ai_prompt,
                image_url=entity.image_url,
                generation_metadata=entity.generation_metadata,
                feedback=entity.feedback,
                revision_notes=entity.revision_notes,
                updated_at=entity.updated_at,
            )
        )

        # Fetch updated model
        result = await self.session.execute(select(PanelModel).where(PanelModel.id == entity.id))
        model = result.scalar_one()

        logger.info(f"Panel updated: {entity.id}")
        return self._to_domain(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a panel by ID."""
        result = await self.session.execute(select(PanelModel).where(PanelModel.id == entity_id))
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            logger.info(f"Panel deleted: {entity_id}")
            return True

        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Panel]:
        """List all panels with pagination."""
        result = await self.session.execute(
            select(PanelModel).limit(limit).offset(offset).order_by(PanelModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]
