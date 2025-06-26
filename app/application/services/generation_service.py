# app/application/services/generation_service.py
"""
Generation orchestration service for webtoon and panel generation.

This module provides the GenerationService class which coordinates AI-powered
generation tasks including story creation, character generation, scene composition,
and image rendering. It serves as the central orchestration layer between the
application's API and the various AI providers and repositories.

Key Features:
- Webtoon generation from text prompts
- Panel generation with AI-assisted scene composition
- Character creation and customization
- Background and environment generation
- Integration with multiple AI providers
- Progress tracking and error handling

Example:
    ```python
    # Using the factory function
    service = create_generation_service(
        ai_provider=ai_provider,
        image_generator=image_generator,
        webtoon_repository=webtoon_repo,
        task_repository=task_repo,
    )
    
    # Or via dependency injection
    def get_generation_service(
        ai_provider: AIProvider = Depends(get_ai_provider),
        image_generator: ImageGenerator = Depends(get_image_generator),
        webtoon_repo: WebtoonRepository = Depends(get_webtoon_repository),
        task_repo: TaskRepository = Depends(get_task_repository),
    ) -> GenerationService:
        return create_generation_service(
            ai_provider=ai_provider,
            image_generator=image_generator,
            webtoon_repository=webtoon_repo,
            task_repository=task_repo,
        )
    ```
"""
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from app.application.dto.generation_dto import GenerationRequestDTO, GenerationResultDTO
from app.application.interfaces.ai_provider import AIProvider
from app.application.interfaces.image_generator import ImageGenerator
from app.application.services.base_service import BaseService
from app.core.error_handling.base_error_handler import BaseErrorHandler
from app.core.logging import get_logger
from app.domain.entities.character import Character, CharacterAppearance
from app.domain.entities.generation_task import GenerationTask, TaskProgress, TaskStatus, TaskType
from app.domain.entities.panel import Panel, SpeechBubble
from app.domain.entities.scene import Scene
from app.domain.entities.webtoon import Webtoon
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
from app.domain.value_objects.position import Position
from app.domain.value_objects.style import StyleConfiguration


def create_generation_service(
    ai_provider: Any,
    image_generator: Any,
    webtoon_repository: WebtoonRepository,
    task_repository: TaskRepository,
    error_handler: Optional[BaseErrorHandler] = None,
    logger: Optional[logging.Logger] = None,
) -> 'GenerationService':
    """
    Factory function to create a GenerationService instance with proper dependency injection.
    
    Args:
        ai_provider: The AI provider for content generation
        image_generator: The image generation service
        webtoon_repository: Repository for webtoon data
        task_repository: Repository for tracking generation tasks
        error_handler: Optional error handler instance
        logger: Optional logger instance
        
    Returns:
        GenerationService: Configured instance of GenerationService
    """
    if logger is None:
        logger = get_logger(__name__)
        
    return GenerationService(
        ai_provider=ai_provider,
        image_generator=image_generator,
        webtoon_repository=webtoon_repository,
        task_repository=task_repository,
        error_handler=error_handler,
        logger=logger,
    )


class GenerationService(BaseService):
    """
    Service for orchestrating webtoon and panel generation.
    
    This service coordinates the generation of webtoon content including:
    - Story and plot development from text prompts
    - Character creation, customization, and management
    - Scene composition and panel generation
    - AI-assisted image rendering and styling
    - Background and environment generation
    - Progress tracking and task management
    
    The service follows the dependency injection pattern and is designed to work
    with different AI providers and storage backends. It inherits from BaseService
    for consistent error handling and logging.
    
    Attributes:
        ai_provider (AIProvider): The AI provider for text generation
        image_generator (ImageGenerator): The image generation service
        webtoon_repository (WebtoonRepository): Repository for webtoon data
        task_repository (TaskRepository): Repository for tracking generation tasks
        logger (Logger): Logger instance for the service
    
    Example:
        ```python
        # Initialize with required dependencies
        service = GenerationService(
            ai_provider=OpenAIProvider(api_key="..."),
            image_generator=StabilityProvider(api_key="..."),
            webtoon_repository=webtoon_repo,
            task_repository=task_repo,
        )
        
        # Start a generation task
        result = await service.start_webtoon_generation(
            GenerationRequestDTO(
                prompt="A fantasy adventure about a young mage",
                art_style="anime",
                num_panels=5
            )
        )
        ```
    """

    def __init__(
        self,
        ai_provider: AIProvider,
        image_generator: ImageGenerator,
        webtoon_repository: WebtoonRepository,
        task_repository: TaskRepository,
        error_handler: Optional[BaseErrorHandler] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the generation service.
        
        Args:
            ai_provider: The AI provider for content generation
            image_generator: The image generation service
            webtoon_repository: Repository for webtoon data
            task_repository: Repository for tracking generation tasks
            error_handler: Optional error handler instance
            logger: Optional logger instance
        """
        # Initialize with the provided logger or create a new one
        super().__init__(error_handler=error_handler, logger=logger or logging.getLogger(__name__))
        self.ai_provider = ai_provider
        self.image_generator = image_generator
        self.webtoon_repository = webtoon_repository
        self.task_repository = task_repository

    async def start_webtoon_generation(
        self, request: GenerationRequestDTO
    ) -> GenerationResultDTO:
        """
        Start an asynchronous webtoon generation task.
        
        This method initiates a background task to generate a complete webtoon based on the provided
        request parameters. It creates a placeholder webtoon and returns immediately with task information.
        The actual generation happens asynchronously.
        
        The generation process includes:
        1. Creating a placeholder webtoon entry
        2. Initializing a generation task
        3. Starting the background generation process
        4. Returning task information for progress tracking
        
        Args:
            request: The generation request DTO containing:
                - prompt: The main story prompt/idea
                - art_style: Desired art style (e.g., 'anime', 'manga')
                - num_panels: Number of panels to generate
                - character_descriptions: Optional list of character descriptions
                - additional_context: Additional context for the story
                - style_preferences: Visual style preferences
            
        Returns:
            GenerationResultDTO: Contains:
                - task_id: ID for tracking generation progress
                - webtoon_id: ID of the generated webtoon
                - status: Initial task status
                - progress_percentage: Initial progress (0%)
                - current_operation: Description of current operation
            
        Raises:
            ValueError: If the request is invalid (missing required fields, etc.)
            ServiceError: If there's an error initializing the generation task
            
        Example:
            ```python
            result = await generation_service.start_webtoon_generation(
                GenerationRequestDTO(
                    prompt="A sci-fi adventure on Mars",
                    art_style="cyberpunk",
                    num_panels=8,
                    character_descriptions=["brave astronaut", "AI companion"],
                    additional_context="The story should have a twist ending"
                )
            )
            print(f"Started generation task {result.task_id} for webtoon {result.webtoon_id}")
            ```
        """
        context = {
            "prompt_length": len(request.prompt) if request.prompt else 0,
            "num_panels": request.num_panels,
            "art_style": str(request.art_style),
        }
        
        try:
            self.logger.info(
                f"Starting webtoon generation with prompt: {request.prompt[:100]}..."
            )
            
            # Import locally to avoid circular imports
            from app.domain.constants.art_styles import ensure_art_style_string
            
            # Create a placeholder webtoon entity first
            from app.domain.entities.webtoon import Webtoon
            
            # Create a placeholder webtoon with minimal information
            placeholder_webtoon = Webtoon(
                title=f"Generating: {request.prompt[:30]}...",
                description=f"Webtoon being generated from prompt: {request.prompt}",
                art_style=ensure_art_style_string(request.art_style)
            )
            
            # Save the placeholder webtoon to get an ID
            saved_webtoon = await self.webtoon_repository.save(placeholder_webtoon)
            webtoon_id = saved_webtoon.id
            
            self.logger.info(
                f"Created placeholder webtoon with ID {webtoon_id}",
                extra={"webtoon_id": webtoon_id}
            )
            
            # Create the task with the webtoon_id included in input_data
            task = GenerationTask(
                task_type=TaskType.WEBTOON_GENERATION,
                input_data={
                    "prompt": request.prompt,
                    "art_style": ensure_art_style_string(request.art_style),
                    "num_panels": request.num_panels,
                    "character_descriptions": request.character_descriptions or [],
                    "additional_context": request.additional_context,
                    "style_preferences": request.style_preferences or {},
                    "webtoon_id": str(webtoon_id),
                },
                progress=TaskProgress(total_steps=5),  # Story, Characters, Scenes, Images, Assembly
            )

            await self.task_repository.save(task)
            self.logger.debug(
                f"Created generation task {task.id} for webtoon {webtoon_id}",
                extra={"task_id": task.id, "webtoon_id": webtoon_id}
            )

            return GenerationResultDTO(
                task_id=task.id,
                webtoon_id=webtoon_id,
                status=task.status.value,
                progress_percentage=task.progress.percentage,
                current_operation="Starting generation...",
            )
            
        except Exception as e:
            error_msg = f"Failed to start webtoon generation: {str(e)}"
            self.logger.error(error_msg, exc_info=True, extra=context)
            self.handle_error(e, context=context)
            raise

    async def start_panel_generation(
        self,
        scene_description: str,
        art_style: str,
        character_names: List[str] = None,
        panel_size: str = "full",
        mood: str = None,
        prompt: str = None,
        style_preferences: Dict[str, Any] = None,
    ) -> GenerationResultDTO:
        """
        Start a single panel generation task.
        
        This method generates a single comic panel based on the provided scene description
        and style parameters. It's useful for generating individual panels or testing
        different compositions.
        
        The generation process includes:
        1. Validating input parameters
        2. Creating a generation task
        3. Composing the scene based on description
        4. Generating the panel image
        5. Returning the result with the generated panel
        
        Args:
            scene_description: Detailed description of the scene to generate.
                Should include key visual elements, composition, and action.
            art_style: Visual style for the panel (e.g., 'anime', 'watercolor').
                Must be one of the supported art styles.
            character_names: Optional list of character names in the scene.
                Helps with character consistency in the generation.
            panel_size: Size of the panel. Must be one of:
                - 'small': 400x300px
                - 'medium': 800x600px
                - 'large': 1200x900px
                - 'full': 1600x1200px (default)
            mood: Desired emotional tone (e.g., 'epic', 'mysterious', 'romantic').
                Influences lighting and composition.
            prompt: Optional override for the full generation prompt.
                If not provided, one will be generated from other parameters.
            style_preferences: Additional style preferences as key-value pairs.
                Common options include:
                - 'color_palette': List of hex color codes
                - 'lighting': Lighting style (e.g., 'dramatic', 'soft')
                - 'perspective': Camera angle (e.g., 'birdseye', 'low_angle')
        
        Returns:
            GenerationResultDTO containing:
                - task_id: ID for tracking generation progress
                - panel_url: URL of the generated panel image
                - status: Generation status
                - progress_percentage: Generation progress (0-100)
                - current_operation: Description of current operation
        
        Raises:
            ValueError: If any parameters are invalid or generation cannot start
            ServiceError: If there's an error during panel generation
            
        Example:
            ```python
            result = await generation_service.start_panel_generation(
                scene_description="A lone astronaut standing on Mars, looking at Earth",
                art_style="realistic",
                character_names=["astronaut"],
                panel_size="large",
                mood="lonely",
                style_preferences={
                    'color_palette': ['#2c3e50', '#e74c3c'],
                    'lighting': 'dramatic_side'
                }
            )
            print(f"Panel generated at: {result.panel_url}")
            ```
        """
        context = {
            "scene_description_length": len(scene_description) if scene_description else 0,
            "art_style": str(art_style),
            "character_count": len(character_names) if character_names else 0,
            "panel_size": panel_size,
        }
        
        try:
            self.logger.info(
                f"Starting panel generation with scene: {scene_description[:100]}..."
            )
            
            # Import locally to avoid circular imports
            from app.domain.constants.art_styles import ensure_art_style_string
            
            # Validate panel size
            if panel_size not in ["small", "medium", "large", "full"]:
                error_msg = f"Invalid panel size: {panel_size}"
                self.logger.warning(error_msg, extra=context)
                raise ValueError(error_msg)
            
            # Create a task for panel generation
            task = GenerationTask(
                task_type=TaskType.PANEL_GENERATION,
                input_data={
                    "scene_description": scene_description,
                    "art_style": ensure_art_style_string(art_style),
                    "character_names": character_names or [],
                    "panel_size": panel_size,
                    "mood": mood,
                    "prompt": prompt,
                    "style_preferences": style_preferences or {},
                },
                progress=TaskProgress(total_steps=2),  # Scene preparation, Image generation
            )

            await self.task_repository.save(task)
            self.logger.debug(
                f"Created panel generation task {task.id}",
                extra={"task_id": task.id}
            )

            # Prepare request data for Celery task
            panel_request_data = {
                "scene_description": scene_description,
                "art_style": ensure_art_style_string(art_style),
                "character_names": character_names or [],
                "panel_size": panel_size,
                "mood": mood,
                "prompt": prompt,
                "style_preferences": style_preferences or {},
            }
            
            # Submit task to Celery for async processing
            try:
                from app.tasks.generation_tasks import start_panel_generation_task
                start_panel_generation_task.delay(task_id=task.id, request_data=panel_request_data)
                self.logger.debug(
                    f"Submitted panel generation task {task.id} to Celery",
                    extra={"task_id": task.id}
                )
            except Exception as e:
                error_msg = f"Failed to submit Celery task: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                # Update task status to failed
                task.status = TaskStatus.FAILED
                task.progress.message = f"Failed to start task: {str(e)}"
                await self.task_repository.save(task)
                raise
            
            return GenerationResultDTO(
                task_id=task.id,
                status=task.status.value,
                progress_percentage=task.progress.percentage,
                current_operation="Starting panel generation...",
            )
            
        except Exception as e:
            error_msg = f"Failed to start panel generation: {str(e)}"
            self.logger.error(error_msg, exc_info=True, extra=context)
            self.handle_error(e, context=context)
            raise

    async def generate_webtoon_sync(
        self, request: GenerationRequestDTO
    ) -> Dict[str, Any]:
        """
        Generate a webtoon synchronously (for testing/development).
        
        Args:
            request: The generation request DTO
            
        Returns:
            Dict containing the generated webtoon details
            
        Raises:
            RuntimeError: If webtoon generation fails at any step
        """
        context = {
            "prompt_length": len(request.prompt) if request.prompt else 0,
            "num_panels": request.num_panels,
            "art_style": str(request.art_style),
        }
        
        self.logger.info(
            f"Starting synchronous webtoon generation: {request.prompt[:100]}...",
            extra=context
        )

        try:
            # Step 1: Generate story structure
            self.logger.debug("Generating story structure...", extra=context)
            try:
                story_data = await self.ai_provider.generate_story(
                    request.prompt,
                    request.art_style.value,
                    request.additional_context,
                )
                self.logger.debug("Successfully generated story structure", extra=context)
            except Exception as e:
                error_msg = "Failed to generate story structure"
                self.logger.error(error_msg, exc_info=True, extra=context)
                self.handle_error(e, context=context)
                raise RuntimeError(f"{error_msg}: {str(e)}") from e

            # Step 2: Create webtoon entity
            try:
                webtoon = Webtoon(
                    title=story_data.get("title", "Generated Webtoon"),
                    description=story_data.get("plot_summary", ""),
                    art_style=request.art_style,
                )
                self.logger.debug("Created webtoon entity", extra=context)
            except Exception as e:
                error_msg = "Failed to create webtoon entity"
                self.logger.error(error_msg, exc_info=True, extra=context)
                self.handle_error(e, context=context)
                raise RuntimeError(f"{error_msg}: {str(e)}") from e

            # Step 3: Create characters
            try:
                characters_data = story_data.get("main_characters", [])
                self.logger.info(
                    f"Creating {len(characters_data)} characters",
                    extra={"character_count": len(characters_data), **context}
                )
                
                for i, char_data in enumerate(characters_data, 1):
                    try:
                        character = self._create_character_from_data(char_data)
                        webtoon.add_character(character)
                        self.logger.debug(
                            f"Created character {i}/{len(characters_data)}: {character.name}",
                            extra={"character_name": character.name, **context}
                        )
                    except Exception as e:
                        error_msg = f"Failed to create character from data: {str(char_data)}"
                        self.logger.warning(error_msg, exc_info=True, extra=context)
                        # Continue with other characters even if one fails
                        continue
            except Exception as e:
                error_msg = "Failed to process characters"
                self.logger.error(error_msg, exc_info=True, extra=context)
                # Continue with generation even if character creation fails

            # Step 4: Generate scenes and panels
            self.logger.info(
                f"Generating {request.num_panels} panels...",
                extra={"num_panels": request.num_panels, **context}
            )
            
            try:
                scenes_data = await self.ai_provider.generate_scene_descriptions(
                    story_data, request.num_panels
                )
                
                for i, scene_data in enumerate(scenes_data, 1):
                    try:
                        panel = await self._create_panel_from_scene(
                            scene_data, webtoon.characters, request.art_style
                        )
                        webtoon.add_panel(panel)
                        self.logger.debug(
                            f"Generated panel {i}/{len(scenes_data)}",
                            extra={"panel_index": i, "total_panels": len(scenes_data), **context}
                        )
                    except Exception as e:
                        error_msg = f"Failed to generate panel {i+1}"
                        self.logger.warning(error_msg, exc_info=True, extra=context)
                        # Continue with other panels even if one fails
                        continue
            except Exception as e:
                error_msg = "Failed to generate scenes"
                self.logger.error(error_msg, exc_info=True, extra=context)
                # Continue with saving even if scene generation fails

            # Step 5: Save webtoon
            saved_webtoon = await self.webtoon_repository.save(webtoon)
            self.logger.info(
                f"Successfully saved webtoon {saved_webtoon.id}",
                extra={"webtoon_id": saved_webtoon.id, **context}
            )
            
            return {
                "webtoon_id": str(saved_webtoon.id),
                "title": saved_webtoon.title,
                "panel_count": saved_webtoon.panel_count,
                "character_count": saved_webtoon.character_count,
            }

        except Exception as e:
            error_msg = f"Error generating webtoon: {str(e)}"
            self.logger.error(error_msg, exc_info=True, extra=context)
            self.handle_error(e, context=context)
            raise RuntimeError(error_msg) from e

    def _create_character_from_data(self, char_data: Dict[str, Any]) -> Character:
        """
        Create a character entity from AI-generated data.
        
        Args:
            char_data: Dictionary containing character data from AI generation
            
        Returns:
            Character: The created character entity
            
        Raises:
            ValueError: If character data is invalid or missing required fields
        """
        context = {
            "character_name": char_data.get("name", "Unknown"),
            "data_keys": list(char_data.keys()) if char_data else []
        }
        
        try:
            self.logger.debug(
                "Creating character from data",
                extra={"character_name": char_data.get("name"), **context}
            )
            
            # Extract basic character information
            name = char_data.get("name", "Unknown Character")
            description = char_data.get("description", "")
            
            if not name:
                error_msg = "Character name is required"
                self.logger.warning(error_msg, extra=context)
                raise ValueError(error_msg)

            # Parse appearance if available
            appearance = CharacterAppearance()
            try:
                appearance_desc = char_data.get("appearance", "")
                if appearance_desc:
                    # Simple parsing of appearance description
                    appearance.hair_style = char_data.get("hair_style", "")
                    appearance.hair_color = char_data.get("hair_color", "")
                    appearance.eye_color = char_data.get("eye_color", "")
                    appearance.clothing_style = char_data.get("clothing_style", "")
                
                self.logger.debug(
                    f"Created appearance for character: {name}",
                    extra={"character_name": name, "appearance": str(appearance)}
                )
            except Exception as e:
                error_msg = f"Failed to parse character appearance: {str(e)}"
                self.logger.warning(error_msg, exc_info=True, extra=context)
                # Continue with default appearance if parsing fails

            # Create character with basic info
            try:
                character = Character(
                    name=name,
                    description=description,
                    appearance=appearance,
                    personality=char_data.get("personality", {}),
                    backstory=char_data.get("backstory", ""),
                )
                
                self.logger.debug(
                    f"Successfully created character: {name}",
                    extra={"character_id": character.id, "character_name": name}
                )
                
                return character
                
            except Exception as e:
                error_msg = f"Failed to create character entity: {str(e)}"
                self.logger.error(error_msg, exc_info=True, extra=context)
                self.handle_error(e, context=context)
                raise ValueError(f"Invalid character data: {str(e)}") from e
                
        except Exception as e:
            error_msg = f"Failed to process character data: {str(e)}"
            self.logger.error(error_msg, exc_info=True, extra=context)
            self.handle_error(e, context=context)
            raise

    async def _create_panel_from_scene(
        self,
        scene_data: Dict[str, Any],
        characters: List[Character],
        art_style: str,
    ) -> Panel:
        """
        Create a panel entity from scene data.
        
        Args:
            scene_data: Dictionary containing scene description and metadata
            characters: List of available characters in the webtoon
            art_style: The art style to use for the panel
            
        Returns:
            Panel: The created panel entity with scene and dialogue
            
        Raises:
            ValueError: If scene data is invalid or panel creation fails
        """
        context = {
            "scene_characters": len(scene_data.get("characters", [])),
            "dialogue_items": len(scene_data.get("dialogue", [])),
            "art_style": str(art_style),
        }
        
        try:
            self.logger.debug("Creating panel from scene data", extra=context)
            
            # Create scene
            try:
                scene = Scene(
                    description=scene_data.get("visual_description", ""),
                    setting=scene_data.get("setting", ""),
                    mood=scene_data.get("mood", ""),
                    character_names=scene_data.get("characters", []),
                    camera_angle=scene_data.get("camera_angle", "medium"),
                )
                self.logger.debug("Created scene for panel", extra=context)
            except Exception as e:
                error_msg = "Failed to create scene from data"
                self.logger.error(error_msg, exc_info=True, extra=context)
                raise ValueError(f"{error_msg}: {str(e)}") from e

            # Create panel with dimensions
            try:
                panel_size = scene_data.get("panel_size", "full")
                dimensions = PanelDimensions.from_size(PanelSize(panel_size))
                
                panel = Panel(
                    scene=scene,
                    dimensions=dimensions,
                    visual_effects=scene_data.get("special_effects", []),
                )
                self.logger.debug(
                    f"Created panel with size {panel_size}",
                    extra={"width": dimensions.width, "height": dimensions.height, **context}
                )
            except Exception as e:
                error_msg = "Failed to create panel with given dimensions"
                self.logger.error(error_msg, exc_info=True, extra=context)
                raise ValueError(f"{error_msg}: {str(e)}") from e

            # Add speech bubbles from dialogue
            try:
                dialogue_data = scene_data.get("dialogue", [])
                self.logger.debug(
                    f"Adding {len(dialogue_data)} speech bubbles",
                    extra={"dialogue_count": len(dialogue_data), **context}
                )
                
                for i, dialogue in enumerate(dialogue_data):
                    try:
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
                            character_name=character_name, 
                            text=text, 
                            position=position
                        )
                        panel.add_speech_bubble(bubble)
                        
                    except Exception as e:
                        error_msg = f"Failed to add speech bubble {i+1}"
                        self.logger.warning(error_msg, exc_info=True, extra=context)
                        continue  # Skip this bubble but continue with others
                        
            except Exception as e:
                error_msg = "Failed to process dialogue"
                self.logger.error(error_msg, exc_info=True, extra=context)
                # Continue without dialogue if processing fails

            # Generate image if image generator is available
            if self.image_generator and hasattr(self.image_generator, 'is_available') and self.image_generator.is_available():
                await self._generate_panel_image(panel, art_style, context)
            else:
                self.logger.debug("Image generator not available, skipping image generation", extra=context)

            return panel
            
        except Exception as e:
            error_msg = f"Failed to create panel from scene: {str(e)}"
            self.logger.error(error_msg, exc_info=True, extra=context)
            self.handle_error(e, context=context)
            raise
            
    async def _generate_panel_image(
        self,
        panel: Panel,
        art_style: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Generate an image for the panel using the configured image generator.
        
        Args:
            panel: The panel to generate an image for
            art_style: The art style to use for generation
            context: Logging context
        """
        try:
            # Ensure art_style is a string
            art_style_str = (
                art_style 
                if isinstance(art_style, str) 
                else getattr(art_style, 'value', str(art_style))
            )
            
            self.logger.debug(
                "Generating panel image",
                extra={"art_style": art_style_str, **context}
            )
            
            style_config = StyleConfiguration.for_style(art_style_str)
            
            # Enhance the visual description
            enhanced_prompt = await self.ai_provider.enhance_visual_description(
                panel.scene.get_prompt_description(),
                art_style_str,
                {"style_config": style_config.to_prompt_text()},
            )
            
            # Generate the image
            local_path, public_url = await self.image_generator.generate_image(
                enhanced_prompt,
                panel.dimensions.width,
                panel.dimensions.height,
                art_style_str,
            )
            
            # Update panel with generated image
            panel.image_url = public_url
            panel.generated_at = datetime.now(UTC)
            
            self.logger.debug(
                "Successfully generated panel image",
                extra={
                    "image_url": public_url,
                    "local_path": str(local_path),
                    **context
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to generate panel image: {str(e)}"
            self.logger.warning(error_msg, exc_info=True, extra=context)
            # Don't fail the whole panel creation if image generation fails
