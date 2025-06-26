# app/application/services/webtoon_service.py
"""
Webtoon business logic service
"""
import logging
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from app.application.dto.webtoon_dto import CharacterDTO, PanelDTO, WebtoonDTO
from app.application.services.base_service import BaseService
from app.core.error_handling.base_error_handler import BaseErrorHandler
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


class WebtoonService(BaseService):
    """Service for webtoon business operations"""

    def __init__(
        self, 
        repository: WebtoonRepository, 
        renderer: WebtoonRenderer,
        error_handler: Optional[BaseErrorHandler] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the webtoon service.
        
        Args:
            repository: The webtoon repository for data access
            renderer: The renderer for generating webtoon output
            error_handler: Optional error handler instance
            logger: Optional logger instance
        """
        # Initialize with the provided logger or create a new one
        super().__init__(error_handler=error_handler, logger=logger or logging.getLogger(__name__))
        self.repository = repository
        self.renderer = renderer
        self.dto_mapper = WebtoonDTOMapper()

    async def create_webtoon(
        self, title: str, description: str, art_style: str
    ) -> WebtoonDTO:
        """
        Create a new webtoon
        
        Args:
            title: The title of the webtoon
            description: A description of the webtoon
            art_style: The art style to use for the webtoon
            
        Returns:
            WebtoonDTO: The created webtoon data transfer object
            
        Raises:
            ValueError: If the webtoon data is invalid
        """
        try:
            self.logger.info(f"Creating new webtoon with title: {title}")
            webtoon = Webtoon(title=title, description=description, art_style=art_style)
            # Save the webtoon using the repository's save method
            saved_webtoon = await self.repository.save(webtoon)
            self.logger.info(f"Successfully created webtoon with ID: {saved_webtoon.id}")
            return self.dto_mapper.to_dto(saved_webtoon)
        except Exception as e:
            error_context = {
                "title": title,
                "description": description,
                "art_style": art_style
            }
            self.handle_error(e, context=error_context)
            raise

    async def get_webtoon(self, webtoon_id: UUID) -> Optional[WebtoonDTO]:
        """
        Get a webtoon by ID
        
        Args:
            webtoon_id: The ID of the webtoon to retrieve
            
        Returns:
            Optional[WebtoonDTO]: The webtoon DTO if found, None otherwise
        """
        try:
            self.logger.debug(f"Retrieving webtoon with ID: {webtoon_id}")
            webtoon = await self.repository.get_by_id(webtoon_id)
            if webtoon:
                return self.dto_mapper.to_dto(webtoon)
            self.logger.warning(f"Webtoon not found with ID: {webtoon_id}")
            return None
        except Exception as e:
            self.handle_error(e, context={"webtoon_id": str(webtoon_id)})
            raise

    async def add_character(
        self, 
        webtoon_id: UUID, 
        name: str,
        description: str,
        appearance_data: Dict[str, Any],
        personality_traits: List[str],
        role: str
    ) -> Optional[WebtoonDTO]:
        """
        Add a character to a webtoon
        
        Args:
            webtoon_id: The ID of the webtoon to add the character to
            name: The character's name
            description: A description of the character
            appearance_data: Dictionary containing appearance details
            personality_traits: List of personality traits
            role: The character's role in the webtoon
            
        Returns:
            Optional[WebtoonDTO]: The updated webtoon DTO, or None if webtoon not found
            
        Raises:
            ValueError: If character data is invalid
        """
        try:
            self.logger.info(f"Adding character '{name}' to webtoon ID: {webtoon_id}")
            webtoon = await self.repository.get_by_id(webtoon_id)
            if not webtoon:
                self.logger.warning(f"Webtoon not found with ID: {webtoon_id}")
                return None
                
            character = Character.create(name, description, appearance_data, personality_traits, role)
            webtoon.add_character(character)
            
            updated_webtoon = await self.repository.update(webtoon.id, webtoon)
            self.logger.info(
                f"Successfully added character '{name}' (ID: {character.id}) "
                f"to webtoon ID: {webtoon_id}"
            )
            return self.dto_mapper.to_dto(updated_webtoon)
            
        except Exception as e:
            error_context = {
                "webtoon_id": str(webtoon_id),
                "character_name": name,
                "role": role
            }
            self.handle_error(e, context=error_context)
            raise

    async def add_panel(
        self, 
        webtoon_id: UUID, 
        scene_description: str,
        character_names: List[str],
        panel_size: str = "medium"
    ) -> Optional[WebtoonDTO]:
        """
        Add a panel to a webtoon
        
        Args:
            webtoon_id: The ID of the webtoon to add the panel to
            scene_description: Description of the panel's scene
            character_names: List of character names in the panel
            panel_size: Size of the panel (small, medium, large)
            
        Returns:
            Optional[WebtoonDTO]: The updated webtoon DTO, or None if webtoon not found
            
        Raises:
            ValueError: If panel data is invalid
        """
        try:
            self.logger.info(f"Adding panel to webtoon ID: {webtoon_id}")
            webtoon = await self.repository.get_by_id(webtoon_id)
            if not webtoon:
                self.logger.warning(f"Webtoon not found with ID: {webtoon_id}")
                return None
                
            panel = webtoon.add_panel(scene_description, character_names, panel_size)
            
            updated_webtoon = await self.repository.update(webtoon.id, webtoon)
            self.logger.info(
                f"Successfully added panel (ID: {panel.id}) to webtoon ID: {webtoon_id}"
            )
            return self.dto_mapper.to_dto(updated_webtoon)
            
        except Exception as e:
            error_context = {
                "webtoon_id": str(webtoon_id),
                "character_count": len(character_names),
                "panel_size": panel_size
            }
            self.handle_error(e, context=error_context)
            raise

    async def publish_webtoon(self, webtoon_id: UUID) -> Optional[WebtoonDTO]:
        """
        Publish a webtoon
        
        Args:
            webtoon_id: The ID of the webtoon to publish
            
        Returns:
            Optional[WebtoonDTO]: The published webtoon DTO, or None if webtoon not found
            
        Raises:
            ValueError: If webtoon cannot be published (e.g., missing required fields)
        """
        try:
            self.logger.info(f"Publishing webtoon ID: {webtoon_id}")
            webtoon = await self.repository.get_by_id(webtoon_id)
            if not webtoon:
                self.logger.warning(f"Webtoon not found with ID: {webtoon_id}")
                return None
                
            webtoon.publish()
            updated_webtoon = await self.repository.update(webtoon.id, webtoon)
            self.logger.info(f"Successfully published webtoon ID: {webtoon_id}")
            return self.dto_mapper.to_dto(updated_webtoon)
            
        except Exception as e:
            self.handle_error(e, context={"webtoon_id": str(webtoon_id)})
            raise

    async def get_all_webtoons(self) -> List[WebtoonDTO]:
        """Get all webtoons"""
        webtoons = await self.repository.get_all()
        return [self.dto_mapper.to_dto(w) for w in webtoons]

    async def search_webtoons(self, keyword: str) -> List[WebtoonDTO]:
        """
        Search webtoons by keyword
        
        Args:
            keyword: The search term to filter webtoons
            
        Returns:
            List[WebtoonDTO]: List of matching webtoon DTOs
        """
        try:
            self.logger.info(f"Searching webtoons for keyword: '{keyword}'")
            webtoons = await self.repository.search(keyword)
            self.logger.debug(f"Found {len(webtoons)} webtoons matching keyword: '{keyword}'")
            return [self.dto_mapper.to_dto(webtoon) for webtoon in webtoons]
        except Exception as e:
            self.handle_error(e, context={"search_keyword": keyword})
            raise

    async def get_webtoon_html_content(self, webtoon_id: UUID) -> Optional[str]:
        """
        Get HTML content for rendering a webtoon
        
        Args:
            webtoon_id: The ID of the webtoon to render
            
        Returns:
            Optional[str]: The rendered HTML content, or None if webtoon not found
        """
        try:
            # First get the webtoon entity
            webtoon = await self.repository.get_by_id(webtoon_id)
            if not webtoon:
                self.logger.warning(f"Webtoon {webtoon_id} not found")
                return None
                
            # Use the renderer to generate HTML
            html_content = self.renderer.render_webtoon(webtoon)
            
            # Add CSS styles
            css_styles = self.renderer.render_css_styles()
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{webtoon.title}</title>
                <style>
                    {css_styles}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            return full_html.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating HTML for webtoon {webtoon_id}: {str(e)}", exc_info=True)
            raise


def get_webtoon_service(
    repository: WebtoonRepository,
    renderer: WebtoonRenderer,
    error_handler: Optional[BaseErrorHandler] = None,
    logger: Optional[logging.Logger] = None
) -> WebtoonService:
    """
    Factory function to create a WebtoonService instance.
    
    Args:
        repository: The webtoon repository for data access
        renderer: The renderer for generating webtoon output
        error_handler: Optional error handler instance
        logger: Optional logger instance
        
    Returns:
        WebtoonService: A configured instance of WebtoonService
    """
    return WebtoonService(
        repository=repository,
        renderer=renderer,
        error_handler=error_handler,
        logger=logger
    )

