# app/application/services/scene_service.py
"""
Scene processing service
"""
import logging
from typing import Dict, List

from app.application.interfaces.ai_provider import AIProvider
from app.domain.entities.character import Character
from app.domain.entities.scene import Scene

logger = logging.getLogger(__name__)


class SceneService:
    """Service for scene processing and enhancement"""

    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    async def enhance_scene(
        self, scene: Scene, characters: List[Character], art_style: str
    ) -> Scene:
        """Enhance a scene with additional details"""
        try:
            # Get character details for scene enhancement
            character_context = self._build_character_context(
                characters, scene.character_names
            )

            # Enhance the scene description
            enhanced_description = await self.ai_provider.enhance_visual_description(
                scene.get_prompt_description(),
                art_style,
                {"characters": character_context, "mood": scene.mood},
            )

            # Update scene with enhanced description
            scene.description = enhanced_description

            return scene

        except Exception as e:
            logger.error(f"Error enhancing scene: {str(e)}")
            return scene

    def _build_character_context(
        self, characters: List[Character], scene_character_names: List[str]
    ) -> Dict[str, str]:
        """Build character context for scene enhancement"""
        context = {}

        for char_name in scene_character_names:
            character = next((c for c in characters if c.name == char_name), None)
            if character:
                context[char_name] = character.get_full_description()
            else:
                context[char_name] = f"Character named {char_name}"

        return context

    async def validate_scene_composition(self, scene: Scene) -> List[str]:
        """Validate scene composition and return suggestions"""
        issues = []

        # Check if scene has characters
        if not scene.character_names:
            issues.append("Scene has no characters defined")

        # Check if scene has description
        if not scene.description:
            issues.append("Scene lacks visual description")

        # Check for reasonable character count
        if len(scene.character_names) > 5:
            issues.append("Too many characters in one scene (recommended: 1-5)")

        # Check mood consistency
        if scene.mood and scene.lighting:
            mood_lighting_map = {
                "happy": ["bright", "natural", "warm"],
                "sad": ["dim", "soft", "cool"],
                "tense": ["dramatic", "harsh", "dark"],
                "mysterious": ["dark", "dramatic", "moody"],
            }

            if scene.mood in mood_lighting_map:
                recommended_lighting = mood_lighting_map[scene.mood]
                if scene.lighting not in recommended_lighting:
                    issues.append(
                        f"Lighting '{scene.lighting}' may not match mood '{scene.mood}'"
                    )

        return issues
