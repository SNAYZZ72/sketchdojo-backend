# app/application/services/character_service.py
"""
Character management service
"""
import logging
from typing import Any, Dict, List, Optional

from app.application.interfaces.ai_provider import AIProvider
from app.domain.entities.character import Character, CharacterAppearance

logger = logging.getLogger(__name__)


class CharacterService:
    """Service for character management and generation"""

    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    async def generate_character_from_description(
        self, name: str, description: str, role: str = "character"
    ) -> Character:
        """Generate a detailed character from a basic description"""
        try:
            # Use AI to expand character details
            enhanced_details = await self._enhance_character_details(
                name, description, role
            )

            # Create appearance from details
            appearance = self._parse_appearance(enhanced_details.get("appearance", {}))

            # Create character
            character = Character(
                name=name,
                description=enhanced_details.get("description", description),
                appearance=appearance,
                personality_traits=enhanced_details.get("personality_traits", []),
                role=role,
                backstory=enhanced_details.get("backstory", ""),
                goals=enhanced_details.get("goals", []),
            )

            return character

        except Exception as e:
            logger.error(f"Error generating character: {str(e)}")
            # Return basic character if enhancement fails
            return Character(name=name, description=description, role=role)

    async def _enhance_character_details(
        self, name: str, description: str, role: str
    ) -> Dict[str, Any]:
        """Use AI to enhance character details"""
        # This would use the AI provider to generate detailed character information
        # For now, return a basic structure
        return {
            "description": description,
            "appearance": {
                "height": "average",
                "build": "normal",
                "hair_color": "brown",
                "eye_color": "brown",
            },
            "personality_traits": ["determined", "brave"],
            "backstory": f"{name} is a {role} in this story.",
            "goals": ["Complete their mission"],
        }

    def _parse_appearance(self, appearance_data: Dict[str, Any]) -> CharacterAppearance:
        """Parse appearance data into CharacterAppearance object"""
        return CharacterAppearance(
            height=appearance_data.get("height", ""),
            build=appearance_data.get("build", ""),
            hair_color=appearance_data.get("hair_color", ""),
            hair_style=appearance_data.get("hair_style", ""),
            eye_color=appearance_data.get("eye_color", ""),
            skin_tone=appearance_data.get("skin_tone", ""),
            distinctive_features=appearance_data.get("distinctive_features", []),
            clothing_style=appearance_data.get("clothing_style", ""),
        )

    def validate_character_consistency(
        self, character: Character, scene_context: Dict[str, Any]
    ) -> List[str]:
        """Validate character consistency within scene context"""
        issues = []

        # Check if character name is present
        if not character.name:
            issues.append("Character must have a name")

        # Check role consistency
        if (
            character.role == "protagonist"
            and scene_context.get("scene_type") == "background"
        ):
            issues.append(
                "Protagonist should not be in background scenes without purpose"
            )

        # Check appearance completeness for main characters
        if character.role in ["protagonist", "antagonist"]:
            if not character.appearance.to_description():
                issues.append(
                    f"Main character '{character.name}' lacks appearance details"
                )

        return issues

    async def generate_character_relationships(
        self, characters: List[Character]
    ) -> Dict[str, Dict[str, str]]:
        """Generate relationships between characters"""
        relationships = {}

        for character in characters:
            relationships[character.name] = {}

            for other_character in characters:
                if character.id != other_character.id:
                    # Simple relationship generation based on roles
                    relationship = self._determine_relationship(
                        character, other_character
                    )
                    if relationship:
                        relationships[character.name][
                            other_character.name
                        ] = relationship

        return relationships

    def _determine_relationship(
        self, char1: Character, char2: Character
    ) -> Optional[str]:
        """Determine relationship between two characters based on their roles"""
        role_relationships = {
            ("protagonist", "antagonist"): "enemy",
            ("protagonist", "supporting"): "ally",
            ("protagonist", "love_interest"): "romantic",
            ("supporting", "supporting"): "friend",
        }

        return role_relationships.get((char1.role, char2.role))
