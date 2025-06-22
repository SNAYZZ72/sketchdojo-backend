"""
Webtoon data mapper for serialization and deserialization
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.domain.entities.character import Character
from app.domain.entities.panel import Panel, SpeechBubble
from app.domain.value_objects.dimensions import PanelDimensions
from app.domain.value_objects.position import Position
from app.domain.entities.webtoon import Webtoon

logger = logging.getLogger(__name__)


class WebtoonDataMapper:
    """
    Handles serialization and deserialization of webtoon-related entities
    between domain entities and storage layer data formats
    """

    def to_dict(self, webtoon: Webtoon) -> dict:
        """Convert a Webtoon entity to a dictionary for storage"""
        # Handle art_style as either string or enum with value attribute
        art_style = webtoon.art_style
        if hasattr(art_style, 'value'):
            art_style = art_style.value
            
        return {
            "id": str(webtoon.id),
            "title": webtoon.title,
            "description": webtoon.description,
            "art_style": art_style,
            "created_at": webtoon.created_at.isoformat(),
            "updated_at": webtoon.updated_at.isoformat(),
            "is_published": webtoon.is_published,
            "metadata": webtoon.metadata,
            "panels": [self._panel_to_dict(panel) for panel in webtoon.panels],
            "characters": [
                self._character_to_dict(char) for char in webtoon.characters
            ],
        }

    def from_dict(self, data: Dict) -> Optional[Webtoon]:
        """Convert a dictionary from storage to a Webtoon entity"""
        if not data:
            return None
            
        try:
            # Parse dates safely
            try:
                created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now()
            except (ValueError, TypeError):
                logger.warning(f"Invalid created_at format: {data.get('created_at')}")
                created_at = datetime.now()
                
            try:
                updated_at = datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else datetime.now()
            except (ValueError, TypeError):
                logger.warning(f"Invalid updated_at format: {data.get('updated_at')}")
                updated_at = datetime.now()
            
            # Create the webtoon entity
            webtoon = Webtoon(
                id=UUID(data.get("id")) if data.get("id") else uuid4(),
                title=data.get("title", ""),
                description=data.get("description", ""),
                art_style=data.get("art_style", "webtoon"),
                created_at=created_at,
                updated_at=updated_at,
                is_published=data.get("is_published", False),
                metadata=data.get("metadata", {}),
            )
            
            # Process panels
            panels = []
            for panel_data in data.get("panels", []):
                try:
                    panel = self._dict_to_panel(panel_data)
                    panels.append(panel)
                except Exception as e:
                    logger.error(f"Error deserializing panel: {e}")
            # Sort panels by sequence number
            panels.sort(key=lambda p: p.sequence_number)
            webtoon.panels = panels
                
            # Process characters
            characters = []
            for character_data in data.get("characters", []):
                try:
                    character = self._dict_to_character(character_data)
                    characters.append(character)
                except Exception as e:
                    logger.error(f"Error deserializing character: {e}")
            webtoon.characters = characters
                
            return webtoon
        except Exception as e:
            logger.error(f"Error deserializing webtoon: {e}")
            return None

    def _panel_to_dict(self, panel: Panel) -> dict:
        """Serialize panel entity to dictionary"""
        dimensions_dict = {}
        if hasattr(panel, 'dimensions') and panel.dimensions:
            dimensions_dict = {
                "width": panel.dimensions.width,
                "height": panel.dimensions.height,
                "aspect_ratio": panel.dimensions.aspect_ratio,
            }
            if hasattr(panel.dimensions, 'size'):
                dimensions_dict["size"] = panel.dimensions.size.value if hasattr(panel.dimensions.size, 'value') else panel.dimensions.size
                
        speech_bubbles = []
        if hasattr(panel, 'speech_bubbles'):
            speech_bubbles = [
                {
                    "id": str(bubble.id),
                    "character_name": bubble.character_name,
                    "text": bubble.text,
                    "position": {
                        "x_percent": bubble.position.x_percent,
                        "y_percent": bubble.position.y_percent,
                        "anchor": bubble.position.anchor if hasattr(bubble.position, 'anchor') else "center",
                    },
                    "style": bubble.style,
                    "tail_direction": bubble.tail_direction,
                }
                for bubble in panel.speech_bubbles
            ] if panel.speech_bubbles else []
                
        generated_at = None
        if hasattr(panel, 'generated_at') and panel.generated_at:
            generated_at = panel.generated_at.isoformat()
            
        result = {
            "id": str(panel.id),
            "sequence_number": panel.sequence_number,
            "dimensions": dimensions_dict,
            "speech_bubbles": speech_bubbles,
            "character_ids": [str(char_id) for char_id in panel.character_ids] if hasattr(panel, 'character_ids') else [],
            "dialogue": panel.dialogue if hasattr(panel, 'dialogue') else [],
            "description": panel.description if hasattr(panel, 'description') else "",
            "image_url": panel.image_url if hasattr(panel, 'image_url') else None,
            "generated_at": generated_at,
            "metadata": panel.metadata if hasattr(panel, 'metadata') else {},
        }
        
        # Add optional fields if they exist
        if hasattr(panel, 'visual_effects'):
            result["visual_effects"] = panel.visual_effects
            
        return result

    def _character_to_dict(self, character: Character) -> dict:
        """Serialize character entity to dictionary"""
        result = {
            "id": str(character.id),
            "name": character.name,
            "description": character.description if hasattr(character, 'description') else "",
            "personality": character.personality if hasattr(character, 'personality') else [],
            "backstory": character.backstory if hasattr(character, 'backstory') else "",
            "image_url": character.image_url if hasattr(character, 'image_url') else "",
        }
        
        if hasattr(character, 'metadata'):
            result["metadata"] = character.metadata
            
        return result

    def _dict_to_panel(self, data: Dict) -> Panel:
        """Convert a dictionary to a Panel entity"""
        # Create PanelDimensions object from dimensions data
        dimensions_data = data.get("dimensions", {})
        dimensions = PanelDimensions(
            size=dimensions_data.get("size", "medium"),
            width=dimensions_data.get("width", 800),
            height=dimensions_data.get("height", 600),
            aspect_ratio=dimensions_data.get("aspect_ratio", "4:3")
        )
        
        # Create speech bubbles
        speech_bubbles = []
        for bubble_data in data.get("speech_bubbles", []):
            position_data = bubble_data.get("position", {})
            position = Position(
                x_percent=position_data.get("x_percent", 50),
                y_percent=position_data.get("y_percent", 50),
                anchor=position_data.get("anchor", "center") if "anchor" in position_data else "center"
            )
            
            bubble = SpeechBubble(
                id=UUID(bubble_data.get("id")) if bubble_data.get("id") else uuid4(),
                character_name=bubble_data.get("character_name", ""),
                text=bubble_data.get("text", ""),
                position=position,
                style=bubble_data.get("style", "normal"),
                tail_direction=bubble_data.get("tail_direction", "bottom")
            )
            speech_bubbles.append(bubble)
            
        # Create panel with the collected attributes
        generated_at = None
        if data.get("generated_at"):
            try:
                generated_at = datetime.fromisoformat(data.get("generated_at"))
            except (ValueError, TypeError):
                logger.warning(f"Invalid generated_at format: {data.get('generated_at')}")
                
        panel = Panel(
            id=UUID(data.get("id")) if data.get("id") else uuid4(),
            sequence_number=data.get("sequence_number", 0),
            dimensions=dimensions,
            speech_bubbles=speech_bubbles,
            visual_effects=data.get("visual_effects", []),
            image_url=data.get("image_url"),
            generated_at=generated_at,
            metadata=data.get("metadata", {})
        )
        
        return panel

    def _dict_to_character(self, data: Dict) -> Character:
        """Convert a dictionary to a Character entity"""
        # Handle both old (personality) and new (personality_traits) format
        personality_traits = data.get("personality_traits", data.get("personality", []))
        
        from app.domain.entities.character import CharacterAppearance
        
        # Create appearance object if present in the data
        appearance_data = data.get("appearance", {})
        appearance = CharacterAppearance(
            height=appearance_data.get("height", ""),
            build=appearance_data.get("build", ""),
            hair_color=appearance_data.get("hair_color", ""),
            hair_style=appearance_data.get("hair_style", ""),
            eye_color=appearance_data.get("eye_color", ""),
            skin_tone=appearance_data.get("skin_tone", ""),
            distinctive_features=appearance_data.get("distinctive_features", []),
            clothing_style=appearance_data.get("clothing_style", "")
        )
        
        character = Character(
            id=UUID(data.get("id")) if data.get("id") else uuid4(),
            name=data.get("name", ""),
            description=data.get("description", ""),
            appearance=appearance,
            personality_traits=personality_traits,
            role=data.get("role", ""),
            relationships=data.get("relationships", {}),
            backstory=data.get("backstory", ""),
            goals=data.get("goals", []),
            emotions=data.get("emotions", {})
        )
        return character
