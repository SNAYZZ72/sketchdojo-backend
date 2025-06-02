# app/application/services/generation_service.py
"""
Generation orchestration service
"""
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from app.application.dto.generation_dto import GenerationRequestDTO, GenerationResultDTO
from app.application.interfaces.ai_provider import AIProvider
from app.application.interfaces.image_generator import ImageGenerator
from app.domain.entities.character import Character, CharacterAppearance
from app.domain.entities.generation_task import GenerationTask, TaskProgress, TaskType
from app.domain.entities.panel import Panel, SpeechBubble
from app.domain.entities.scene import Scene
from app.domain.entities.webtoon import Webtoon
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
from app.domain.value_objects.position import Position
from app.domain.value_objects.style import ArtStyle, StyleConfiguration

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for orchestrating webtoon and panel generation"""

    def __init__(
        self,
        ai_provider: AIProvider,
        image_generator: ImageGenerator,
        webtoon_repository: WebtoonRepository,
        task_repository: TaskRepository,
    ):
        self.ai_provider = ai_provider
        self.image_generator = image_generator
        self.webtoon_repository = webtoon_repository
        self.task_repository = task_repository

    async def start_webtoon_generation(
        self, request: GenerationRequestDTO
    ) -> GenerationResultDTO:
        """Start a webtoon generation task"""
        task = GenerationTask(
            task_type=TaskType.WEBTOON_GENERATION,
            input_data={
                "prompt": request.prompt,
                "art_style": request.art_style.value,
                "num_panels": request.num_panels,
                "character_descriptions": request.character_descriptions or [],
                "additional_context": request.additional_context,
                "style_preferences": request.style_preferences or {},
            },
            progress=TaskProgress(
                total_steps=5
            ),  # Story, Characters, Scenes, Images, Assembly
        )

        await self.task_repository.save(task)

        # Start background generation (in real implementation, this would be a Celery task)
        # For now, we'll simulate the process

        return GenerationResultDTO(
            task_id=task.id,
            status=task.status.value,
            progress_percentage=task.progress.percentage,
            current_operation="Starting generation...",
        )

    async def start_panel_generation(
        self,
        scene_description: str,
        art_style: ArtStyle,
        character_names: List[str] = None,
        panel_size: str = "full",
        mood: str = None,
        prompt: str = None,
        style_preferences: Dict[str, Any] = None,
    ) -> GenerationResultDTO:
        """Start a single panel generation task"""
        # Create a task for panel generation
        task = GenerationTask(
            task_type=TaskType.PANEL_GENERATION,
            input_data={
                "scene_description": scene_description,
                "art_style": art_style.value,
                "character_names": character_names or [],
                "panel_size": panel_size,
                "mood": mood,
                "prompt": prompt,
                "style_preferences": style_preferences or {},
            },
            progress=TaskProgress(total_steps=2),  # Scene preparation, Image generation
        )

        await self.task_repository.save(task)

        # This would normally be processed in a background task
        return GenerationResultDTO(
            task_id=task.id,
            status=task.status.value,
            progress_percentage=task.progress.percentage,
            current_operation="Starting panel generation...",
        )

    async def generate_webtoon_sync(
        self, request: GenerationRequestDTO
    ) -> Dict[str, Any]:
        """Generate a webtoon synchronously (for testing/development)"""
        logger.info(f"Starting webtoon generation: {request.prompt}")

        try:
            # Step 1: Generate story structure
            logger.info("Generating story structure...")
            story_data = await self.ai_provider.generate_story(
                request.prompt, request.art_style.value, request.additional_context
            )

            # Step 2: Create webtoon entity
            webtoon = Webtoon(
                title=story_data.get("title", "Generated Webtoon"),
                description=story_data.get("plot_summary", ""),
                art_style=request.art_style,
            )

            # Step 3: Create characters
            characters_data = story_data.get("main_characters", [])
            for char_data in characters_data:
                character = self._create_character_from_data(char_data)
                webtoon.add_character(character)

            # Step 4: Generate scenes and panels
            logger.info(f"Generating {request.num_panels} panels...")
            scenes_data = await self.ai_provider.generate_scene_descriptions(
                story_data, request.num_panels
            )

            for i, scene_data in enumerate(scenes_data):
                panel = await self._create_panel_from_scene(
                    scene_data, webtoon.characters, request.art_style
                )
                webtoon.add_panel(panel)

            # Step 5: Save webtoon
            saved_webtoon = await self.webtoon_repository.save(webtoon)

            logger.info(f"Webtoon generation completed: {saved_webtoon.id}")

            return {
                "webtoon_id": str(saved_webtoon.id),
                "title": saved_webtoon.title,
                "panel_count": saved_webtoon.panel_count,
                "character_count": saved_webtoon.character_count,
            }

        except Exception as e:
            logger.error(f"Error generating webtoon: {str(e)}")
            raise

    def _create_character_from_data(self, char_data: Dict[str, Any]) -> Character:
        """Create a character entity from AI-generated data"""
        name = char_data.get("name", "Unknown Character")
        description = char_data.get("description", "")

        # Parse appearance if available
        appearance_desc = char_data.get("appearance", "")
        appearance = CharacterAppearance()
        if appearance_desc:
            # Simple parsing - in a real system, this would be more sophisticated
            if "tall" in appearance_desc.lower():
                appearance.height = "tall"
            if "short" in appearance_desc.lower():
                appearance.height = "short"
            # Add more parsing logic as needed

        return Character(
            name=name,
            description=description,
            appearance=appearance,
            personality_traits=char_data.get("personality_traits", []),
            role=char_data.get("role", "character"),
        )

    async def _create_panel_from_scene(
        self,
        scene_data: Dict[str, Any],
        characters: List[Character],
        art_style: ArtStyle,
    ) -> Panel:
        """Create a panel entity from scene data"""
        # Create scene
        scene = Scene(
            description=scene_data.get("visual_description", ""),
            setting=scene_data.get("setting", ""),
            mood=scene_data.get("mood", ""),
            character_names=scene_data.get("characters", []),
            camera_angle=scene_data.get("camera_angle", "medium"),
        )

        # Create panel
        dimensions = PanelDimensions.from_size(
            PanelSize(scene_data.get("panel_size", "full"))
        )

        panel = Panel(
            scene=scene,
            dimensions=dimensions,
            visual_effects=scene_data.get("special_effects", []),
        )

        # Add speech bubbles from dialogue
        dialogue_data = scene_data.get("dialogue", [])
        for i, dialogue in enumerate(dialogue_data):
            if isinstance(dialogue, dict):
                character_name = dialogue.get("character", "Character")
                text = dialogue.get("text", "")
            else:
                character_name = "Character"
                text = str(dialogue)

            # Simple positioning - alternate sides
            position = Position.from_named_position(
                "top-left" if i % 2 == 0 else "top-right"
            )

            bubble = SpeechBubble(
                character_name=character_name, text=text, position=position
            )
            panel.add_speech_bubble(bubble)

        # Generate image if image generator is available
        if self.image_generator.is_available():
            try:
                style_config = StyleConfiguration.for_style(art_style)
                enhanced_prompt = await self.ai_provider.enhance_visual_description(
                    scene.get_prompt_description(),
                    art_style.value,
                    {"style_config": style_config.to_prompt_text()},
                )

                local_path, public_url = await self.image_generator.generate_image(
                    enhanced_prompt,
                    panel.dimensions.width,
                    panel.dimensions.height,
                    art_style.value,
                )

                panel.image_url = public_url
                panel.generated_at = datetime.now(UTC)

            except Exception as e:
                logger.warning(f"Failed to generate image for panel: {str(e)}")

        return panel
