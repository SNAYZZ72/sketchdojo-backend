# app/application/services/webtoon_service.py
"""
Webtoon business logic service
"""
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from app.application.dto.webtoon_dto import CharacterDTO, PanelDTO, WebtoonDTO
from app.domain.entities.character import Character
from app.domain.entities.panel import Panel
from app.domain.entities.webtoon import Webtoon
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.utils.webtoon_renderer import WebtoonRenderer


class WebtoonDTOMapper:
    """Mapper for converting between webtoon entities and DTOs"""
    
    @staticmethod
    def to_dto(webtoon: Webtoon) -> WebtoonDTO:
        """Convert webtoon entity to DTO"""
        return WebtoonDTO(
            id=webtoon.id,
            title=webtoon.title,
            description=webtoon.description,
            art_style=webtoon.art_style,
            panels=[WebtoonDTOMapper.panel_to_dto(p) for p in webtoon.panels],
            characters=[WebtoonDTOMapper.character_to_dto(c) for c in webtoon.characters],
            created_at=webtoon.created_at,
            updated_at=webtoon.updated_at,
            is_published=webtoon.is_published,
            panel_count=webtoon.panel_count,
            character_count=webtoon.character_count,
        )

    @staticmethod
    def character_to_dto(character: Character) -> CharacterDTO:
        """Convert character entity to DTO"""
        return CharacterDTO(
            id=character.id,
            name=character.name,
            description=character.description,
            appearance_description=character.appearance.to_description(),
            personality_traits=character.personality_traits,
            role=character.role,
        )

    @staticmethod
    def panel_to_dto(panel: Panel) -> PanelDTO:
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


class WebtoonRenderer(Protocol):
    """Protocol for webtoon rendering implementations"""
    
    def render_webtoon(self, webtoon: Webtoon) -> str:
        """Render a webtoon to HTML"""
        ...
        
    def render_css_styles(self) -> str:
        """Render CSS styles for webtoon"""
        ...


class WebtoonService:
    """Service for webtoon business operations"""

    def __init__(self, repository: WebtoonRepository, renderer: WebtoonRenderer):
        self.repository = repository
        self.renderer = renderer
        self.dto_mapper = WebtoonDTOMapper()

    async def create_webtoon(
        self, title: str, description: str, art_style: str
    ) -> WebtoonDTO:
        """Create a new webtoon"""
        # Create a new webtoon entity directly
        webtoon = Webtoon(
            title=title,
            description=description,
            art_style=art_style
        )

        # Save using the repository's save method
        saved_webtoon = await self.repository.save(webtoon)
        return WebtoonDTOMapper.to_dto(saved_webtoon)

    async def get_webtoon(self, webtoon_id: UUID) -> Optional[WebtoonDTO]:
        """Get a webtoon by ID"""
        webtoon = await self.repository.get_by_id(webtoon_id)
        return WebtoonDTOMapper.to_dto(webtoon) if webtoon else None

    async def add_character(
        self, 
        webtoon_id: UUID, 
        name: str,
        description: str,
        appearance_data: Dict[str, Any],
        personality_traits: List[str],
        role: str
    ) -> Optional[WebtoonDTO]:
        """Add a character to a webtoon using data fields instead of domain entity"""
        # Get the webtoon
        webtoon = await self.repository.get_by_id(webtoon_id)
        if not webtoon:
            return None
            
        # Create character entity
        from app.domain.entities.character import Character, CharacterAppearance
        character = Character(
            name=name,
            description=description,
            appearance=CharacterAppearance(**appearance_data),
            personality_traits=personality_traits,
            role=role,
        )

        # Add character to webtoon
        webtoon.add_character(character)
        saved_webtoon = await self.repository.save(webtoon)
        return WebtoonDTOMapper.to_dto(saved_webtoon)

    async def add_panel(
        self, 
        webtoon_id: UUID, 
        scene_description: str,
        character_names: List[str],
        panel_size: str = "medium"
    ) -> Optional[WebtoonDTO]:
        """Add a panel to a webtoon using data fields instead of domain entity"""
        # Get the webtoon
        webtoon = await self.repository.get_by_id(webtoon_id)
        if not webtoon:
            return None
            
        # Create panel entity
        from app.domain.entities.panel import Panel
        from app.domain.entities.scene import Scene
        from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
        
        # Create the scene
        scene = Scene(
            description=scene_description,
            character_names=character_names,
        )
        
        # Create the panel with appropriate dimensions
        panel = Panel(
            scene=scene,
            dimensions=PanelDimensions.from_size(PanelSize(panel_size)),
        )

        # Add panel to webtoon
        webtoon.add_panel(panel)
        saved_webtoon = await self.repository.save(webtoon)
        return WebtoonDTOMapper.to_dto(saved_webtoon)

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
        return [WebtoonDTOMapper.to_dto(w) for w in webtoons]

    async def search_webtoons(self, keyword: str) -> List[WebtoonDTO]:
        """Search webtoons by keyword"""
        webtoons = await self.repository.search_by_keyword(keyword)
        return [WebtoonDTOMapper.to_dto(w) for w in webtoons]

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



