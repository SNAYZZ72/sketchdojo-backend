# app/application/services/webtoon_service.py
"""
Webtoon business logic service
"""
from typing import List, Optional
from uuid import UUID

from app.application.dto.webtoon_dto import CharacterDTO, PanelDTO, WebtoonDTO
from app.domain.entities.character import Character
from app.domain.entities.panel import Panel
from app.domain.entities.webtoon import Webtoon
from app.domain.repositories.webtoon_repository import WebtoonRepository


class WebtoonService:
    """Service for webtoon business operations"""

    def __init__(self, repository: WebtoonRepository):
        from app.utils.webtoon_renderer import WebtoonRenderer
        self.renderer = WebtoonRenderer()
        self.repository = repository

    async def create_webtoon(
        self, title: str, description: str, art_style: str
    ) -> WebtoonDTO:
        """Create a new webtoon"""
        webtoon = self.repository.create_webtoon(
            title=title, description=description, art_style=art_style
        )

        saved_webtoon = await self.repository.save(webtoon)
        return self._to_dto(saved_webtoon)

    async def get_webtoon(self, webtoon_id: UUID) -> Optional[WebtoonDTO]:
        """Get a webtoon by ID"""
        webtoon = await self.repository.get_by_id(webtoon_id)
        return self._to_dto(webtoon) if webtoon else None

    async def add_character(
        self, webtoon_id: UUID, character: Character
    ) -> Optional[WebtoonDTO]:
        """Add a character to a webtoon"""
        webtoon = await self.repository.get_by_id(webtoon_id)
        if not webtoon:
            return None

        webtoon.add_character(character)
        saved_webtoon = await self.repository.save(webtoon)
        return self._to_dto(saved_webtoon)

    async def add_panel(self, webtoon_id: UUID, panel: Panel) -> Optional[WebtoonDTO]:
        """Add a panel to a webtoon"""
        webtoon = await self.repository.get_by_id(webtoon_id)
        if not webtoon:
            return None

        webtoon.add_panel(panel)
        saved_webtoon = await self.repository.save(webtoon)
        return self._to_dto(saved_webtoon)

    async def publish_webtoon(self, webtoon_id: UUID) -> bool:
        """Publish a webtoon"""
        webtoon = await self.repository.get_by_id(webtoon_id)
        if not webtoon:
            return False

        webtoon.is_published = True
        await self.repository.save(webtoon)
        return True

    async def get_all_webtoons(self) -> List[WebtoonDTO]:
        """Get all webtoons"""
        webtoons = await self.repository.get_all()
        return [self._to_dto(w) for w in webtoons]

    async def search_webtoons(self, keyword: str) -> List[WebtoonDTO]:
        """Search webtoons by keyword"""
        webtoons = await self.repository.search_by_keyword(keyword)
        return [self._to_dto(w) for w in webtoons]

    def _to_dto(self, webtoon: Webtoon) -> WebtoonDTO:
        """Convert webtoon entity to DTO"""
        return WebtoonDTO(
            id=webtoon.id,
            title=webtoon.title,
            description=webtoon.description,
            art_style=webtoon.art_style,
            panels=[self._panel_to_dto(p) for p in webtoon.panels],
            characters=[self._character_to_dto(c) for c in webtoon.characters],
            created_at=webtoon.created_at,
            updated_at=webtoon.updated_at,
            is_published=webtoon.is_published,
            panel_count=webtoon.panel_count,
            character_count=webtoon.character_count,
        )

    def _character_to_dto(self, character: Character) -> CharacterDTO:
        """Convert character entity to DTO"""
        return CharacterDTO(
            id=character.id,
            name=character.name,
            description=character.description,
            appearance_description=character.appearance.to_description(),
            personality_traits=character.personality_traits,
            role=character.role,
        )

    def _panel_to_dto(self, panel: Panel) -> PanelDTO:
        """Convert panel entity to DTO"""
        dialogue = [
            {"character": bubble.character_name, "text": bubble.text}
            for bubble in panel.speech_bubbles
        ]

        return PanelDTO(
            id=panel.id,
            sequence_number=panel.sequence_number,
            scene_description=panel.scene.get_prompt_description(),
            character_names=panel.get_characters_in_panel(),
            dialogue=dialogue,
            visual_effects=panel.visual_effects,
            image_url=panel.image_url,
            generated_at=panel.generated_at,
        )
        
    async def get_webtoon_html_content(self, webtoon_id: UUID) -> Optional[str]:
        """Generate HTML content for a webtoon"""
        webtoon = await self.repository.get_by_id(webtoon_id)
        if not webtoon:
            return None
            
        # Generate HTML using the renderer
        html_content = self.renderer.render_webtoon(webtoon)
        css_styles = self.renderer.render_css_styles()
        
        # Combine CSS and HTML
        full_html = f"{css_styles}\n{html_content}"
        
        return full_html
