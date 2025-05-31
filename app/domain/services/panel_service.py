# =============================================================================
# app/domain/services/panel_service.py
# =============================================================================
import logging
from typing import List
from uuid import UUID

from app.domain.models.panel import Panel, PanelStatus
from app.domain.repositories.panel_repository import PanelRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.schemas.panel import PanelCreate, PanelResponse, PanelUpdate

logger = logging.getLogger(__name__)


class PanelService:
    """Service for panel management."""

    def __init__(self, panel_repository: PanelRepository, webtoon_repository: WebtoonRepository):
        self.panel_repo = panel_repository
        self.webtoon_repo = webtoon_repository

    async def create_panel(
        self, webtoon_id: UUID, user_id: UUID, panel_data: PanelCreate
    ) -> PanelResponse:
        """Create a new panel."""
        # Verify webtoon ownership
        webtoon = await self.webtoon_repo.get_by_id(webtoon_id)
        if not webtoon:
            raise ValueError("Webtoon not found")

        # Would check project ownership here

        # Create panel domain object
        panel = Panel(
            webtoon_id=webtoon_id,
            scene_id=panel_data.scene_id,
            sequence_number=panel_data.sequence_number,
            visual_description=panel_data.visual_description,
            size=panel_data.size,
            layout=panel_data.layout,
            characters_present=panel_data.characters_present or [],
            speech_bubbles=[sb.dict() for sb in panel_data.speech_bubbles],
            visual_elements=[ve.dict() for ve in panel_data.visual_elements],
        )

        # Save to repository
        saved_panel = await self.panel_repo.create(panel)

        logger.info(f"Panel created: {saved_panel.id} for webtoon {webtoon_id}")
        return PanelResponse.model_validate(saved_panel)

    async def get_panel(self, panel_id: UUID, user_id: UUID) -> PanelResponse:
        """Get a panel by ID."""
        panel = await self.panel_repo.get_by_id(panel_id)
        if not panel:
            raise ValueError("Panel not found")

        # Check ownership through webtoon/project
        webtoon = await self.webtoon_repo.get_by_id(panel.webtoon_id)
        if not webtoon:
            raise ValueError("Associated webtoon not found")

        # Would check project ownership here

        return PanelResponse.model_validate(panel)

    async def get_webtoon_panels(self, webtoon_id: UUID, user_id: UUID) -> List[Panel]:
        """Get all panels for a webtoon."""
        # Verify webtoon ownership
        webtoon = await self.webtoon_repo.get_by_id(webtoon_id)
        if not webtoon:
            raise ValueError("Webtoon not found")

        # Would check project ownership here

        panels = await self.panel_repo.get_by_webtoon_id(webtoon_id)
        return panels

    async def update_panel(
        self, panel_id: UUID, user_id: UUID, panel_data: PanelUpdate
    ) -> PanelResponse:
        """Update a panel."""
        panel = await self.panel_repo.get_by_id(panel_id)
        if not panel:
            raise ValueError("Panel not found")

        # Check ownership through webtoon/project
        webtoon = await self.webtoon_repo.get_by_id(panel.webtoon_id)
        if not webtoon:
            raise ValueError("Associated webtoon not found")

        # Would check project ownership here

        # Update panel fields
        update_data = panel_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(panel, field):
                if field in ["speech_bubbles", "visual_elements"] and value:
                    # Convert Pydantic models to dicts
                    if isinstance(value[0], dict):
                        setattr(panel, field, value)
                    else:
                        setattr(panel, field, [item.dict() for item in value])
                else:
                    setattr(panel, field, value)

        # Save changes
        updated_panel = await self.panel_repo.update(panel)

        logger.info(f"Panel updated: {panel_id}")
        return PanelResponse.model_validate(updated_panel)

    async def delete_panel(self, panel_id: UUID, user_id: UUID):
        """Delete a panel."""
        panel = await self.panel_repo.get_by_id(panel_id)
        if not panel:
            raise ValueError("Panel not found")

        # Check ownership through webtoon/project
        webtoon = await self.webtoon_repo.get_by_id(panel.webtoon_id)
        if not webtoon:
            raise ValueError("Associated webtoon not found")

        # Would check project ownership here

        await self.panel_repo.delete(panel_id)

        logger.info(f"Panel deleted: {panel_id}")

    async def mark_panel_generating(self, panel_id: UUID):
        """Mark a panel as currently generating."""
        panel = await self.panel_repo.get_by_id(panel_id)
        if panel:
            panel.mark_generating()
            await self.panel_repo.update(panel)

    async def mark_panel_generated(self, panel_id: UUID, image_url: str):
        """Mark a panel as successfully generated."""
        panel = await self.panel_repo.get_by_id(panel_id)
        if panel:
            panel.mark_generated(image_url)
            await self.panel_repo.update(panel)
