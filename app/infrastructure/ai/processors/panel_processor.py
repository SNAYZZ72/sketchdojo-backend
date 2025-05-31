# =============================================================================
# app/infrastructure/ai/processors/panel_processor.py
# =============================================================================
import logging
from typing import Any, Dict, List, Optional

from app.infrastructure.ai.image.base import BaseImageGenerator, ImageRequest, ImageStyle
from app.infrastructure.ai.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class PanelProcessor:
    """Processes panel generation including visual prompts and image creation."""

    def __init__(self, llm_client: BaseLLMClient, image_generator: BaseImageGenerator):
        self.llm_client = llm_client
        self.image_generator = image_generator

    async def generate_visual_prompt(
        self,
        scene_description: Dict[str, Any],
        characters: List[Dict[str, Any]],
        style: str = "webtoon",
    ) -> str:
        """Generate a detailed visual prompt for image generation."""
        try:
            # Extract character descriptions
            char_descriptions = []
            for char_name in scene_description.get("characters_present", []):
                char_data = next((c for c in characters if c["name"] == char_name), None)
                if char_data:
                    char_descriptions.append(
                        f"{char_name}: {char_data.get('visual_description', char_data.get('description', ''))}"
                    )

            prompt = f"""
            Create a detailed visual prompt for {style} image generation:
            
            Scene: {scene_description['description']}
            Environment: {scene_description.get('environment', {})}
            Characters: {', '.join(char_descriptions)}
            Camera Angle: {scene_description.get('camera_angle', 'medium')}
            Visual Focus: {scene_description.get('visual_focus', '')}
            Mood: {scene_description.get('emotional_beat', '')}
            
            Generate a comprehensive prompt that includes:
            1. Scene composition and layout
            2. Character positions, poses, and expressions
            3. Environmental details and atmosphere
            4. Lighting and color scheme
            5. Art style specifications
            """

            schema = {
                "type": "object",
                "properties": {
                    "visual_prompt": {"type": "string"},
                    "negative_prompt": {"type": "string"},
                    "style_tags": {"type": "array", "items": {"type": "string"}},
                    "composition_notes": {"type": "string"},
                },
                "required": ["visual_prompt"],
            }

            result = await self.llm_client.generate_structured_output(
                prompt, schema, temperature=0.6
            )

            return result["visual_prompt"]

        except Exception as e:
            logger.error(f"Visual prompt generation error: {str(e)}")
            raise

    async def generate_panel_image(
        self,
        visual_prompt: str,
        style: str = "webtoon",
        quality: str = "standard",
        width: int = 1024,
        height: int = 1024,
    ) -> Dict[str, Any]:
        """Generate panel image using the visual prompt."""
        try:
            # Map style string to ImageStyle enum
            style_mapping = {
                "webtoon": ImageStyle.WEBTOON,
                "manga": ImageStyle.MANGA,
                "comic": ImageStyle.COMIC,
                "realistic": ImageStyle.REALISTIC,
                "anime": ImageStyle.ANIME,
            }

            image_style = style_mapping.get(style.lower(), ImageStyle.WEBTOON)

            request = ImageRequest(
                prompt=visual_prompt, style=image_style, quality=quality, width=width, height=height
            )

            response = await self.image_generator.generate_image(request)

            return {
                "image_url": response.image_url,
                "metadata": response.metadata,
                "visual_prompt": visual_prompt,
            }

        except Exception as e:
            logger.error(f"Panel image generation error: {str(e)}")
            raise

    async def generate_complete_panel(
        self,
        scene_description: Dict[str, Any],
        characters: List[Dict[str, Any]],
        style: str = "webtoon",
        quality: str = "standard",
    ) -> Dict[str, Any]:
        """Generate a complete panel with image and metadata."""
        try:
            # Generate visual prompt
            visual_prompt = await self.generate_visual_prompt(scene_description, characters, style)

            # Generate image
            image_result = await self.generate_panel_image(visual_prompt, style, quality)

            # Combine results
            return {
                "scene_data": scene_description,
                "visual_prompt": visual_prompt,
                "image_url": image_result["image_url"],
                "generation_metadata": image_result["metadata"],
                "characters_present": scene_description.get("characters_present", []),
                "dialogue": scene_description.get("dialogue", []),
                "special_effects": scene_description.get("special_effects", []),
            }

        except Exception as e:
            logger.error(f"Complete panel generation error: {str(e)}")
            raise
