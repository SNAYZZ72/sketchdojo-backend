# app/tasks/generation_tasks.py
"""
Background tasks for webtoon and panel generation
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timezone, UTC
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

from app.config import get_settings
from app.dependencies import create_storage_provider
from app.tasks.celery_app import celery_app
# Import Redis publisher for notifications
from app.infrastructure.notifications.redis_publisher import get_redis_publisher
from app.infrastructure.notifications.notification_types import NotificationType
from app.websocket.connection_manager import get_connection_manager  # Keep for backward compatibility
from app.domain.entities.generation_task import TaskStatus
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.application.interfaces.storage_provider import StorageProvider

# Configure root logger to see all debug messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _get_repositories() -> Tuple[StorageProvider, TaskRepository, WebtoonRepository]:
    """Helper function to get consistent storage and repositories for Celery tasks
    Uses the same storage provider creation logic as the main application.
    Returns a tuple of (storage, task_repo, webtoon_repo)
    """
    # Get settings
    settings = get_settings()
    
    # Create storage provider using the centralized function
    storage = create_storage_provider(settings)
    
    # Log storage information
    logger.info(f"Celery task using storage provider: {storage.__class__.__name__}")
    
    # Create repositories with this storage
    from app.domain.mappers.task_mapper import TaskDataMapper
    from app.domain.mappers.webtoon_mapper import WebtoonDataMapper
    
    task_repo = TaskRepository(storage, mapper=TaskDataMapper())
    webtoon_repo = WebtoonRepository(storage, mapper=WebtoonDataMapper())
    
    return storage, task_repo, webtoon_repo


@celery_app.task(bind=True)
def start_webtoon_generation_task(self, task_id: str):
    """Background task for webtoon generation"""
    task_name = self.name
    task_id_celery = self.request.id
    task_retries = self.request.retries
    
    logger.debug(f"CELERY TASK EXECUTION START - Task {task_name} with request ID {task_id_celery}")
    logger.debug(f"Task parameters - task_id: {task_id}")
    logger.debug(f"Environment variables: REDIS_URL={os.environ.get('REDIS_URL')}, CELERY_BROKER_URL={os.environ.get('CELERY_BROKER_URL')}")
    
    try:
        # Initialize storage and repositories using the centralized helper function
        storage, task_repo, webtoon_repo = _get_repositories()
        
        # Retrieve the task from storage - we need its input_data
        # Use sync methods to avoid asyncio.run issues in Celery worker
        task = task_repo.get_by_id_sync(task_id)
        if not task:
            logger.error(f"Task {task_id} not found in storage. Cannot proceed with generation.")
            raise ValueError(f"Task {task_id} not found in storage")
            
        # Extract the request data from the task
        request_data = task.input_data
        
        # Log details about the request data
        logger.debug(f"Request data keys: {list(request_data.keys())}")
        
        # Ensure art_style is a string if present
        if 'art_style' in request_data:
            art_style = request_data['art_style']
            logger.debug(f"ART_STYLE DEBUG - Type: {type(art_style).__name__}, Value: {art_style}")
            
            # Ensure art_style is a string
            if hasattr(art_style, 'value'):
                logger.warning(f"Found ArtStyle enum with value: {art_style.value}")
                request_data['art_style'] = art_style.value
            elif not isinstance(art_style, str):
                logger.warning(f"Converting non-string art_style to string: {art_style}")
                request_data['art_style'] = str(art_style)
        
        # Update task status to IN_PROGRESS before starting
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        # Use synchronous methods for Redis operations in Celery tasks
        try:
            task_repo.save_sync(task)
        except Exception as e:
            logger.error(f"Error saving task {task_id}: {str(e)}")
            raise RuntimeError(f"Failed to save task {task_id}: {str(e)}")
        logger.debug(f"Updated task {task_id} status to IN_PROGRESS")
        
        # Run the async generation in sync context by creating a new event loop
        # since we can't use asyncio.run() in a running event loop
        try:
            # Create a new event loop and set it as the current event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function in this loop and get the result
            # We're passing task_id and the request_data from the retrieved task
            result = loop.run_until_complete(generate_webtoon_async(task_id, request_data))
            
            # Clean up the loop
            loop.close()
            
            logger.debug(f"Asynchronous generation completed for task {task_id}")
        except Exception as e:
            logger.error(f"Error in synchronous generation: {str(e)}")
            raise
        
        # Double-check that task status is updated to COMPLETED
        task = task_repo.get_by_id_sync(task_id)
        if task and task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
            task_repo.save_sync(task)
            logger.debug(f"Double-check update: task {task_id} status set to COMPLETED")
        
        logger.debug(f"CELERY TASK EXECUTION COMPLETE - Task {task_name} with ID {task_id_celery}")
        return result
    except Exception as e:
        logger.error(f"ERROR IN CELERY TASK: {type(e).__name__}: {str(e)}", exc_info=True)
        
        # Try to update task status to FAILED
        try:
            from app.infrastructure.storage.file_storage import FileStorage
            from app.config import get_settings
            settings = get_settings()
            storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "/app/storage"))
            storage = FileStorage(storage_path)
            task_repo = TaskRepository(storage)
            
            # Use sync methods to avoid asyncio.run issues in Celery worker
            task = task_repo.get_by_id_sync(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)
                # Use sync methods to avoid asyncio.run issues
                task_repo.save_sync(task)
                logger.debug(f"Updated task {task_id} status to FAILED")
        except Exception as inner_e:
            logger.error(f"Failed to update task status to FAILED: {str(inner_e)}", exc_info=True)
            
        # Notify WebSocket clients of failure via Redis
        try:
            # Get Redis publisher
            notification_publisher = get_redis_publisher()
            
            # Publish task failure notification
            notification_publisher.publish(
                NotificationType.TASK_FAILED,
                {
                    "task_id": task_id,
                    "error": str(e)
                }
            )
            logger.info(f"Published task failure notification for task {task_id}")
        except Exception as notification_error:
            logger.error(f"Failed to publish task failure notification: {str(notification_error)}")
            
        raise


async def generate_webtoon_async(
    task_id: str, request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Async webtoon generation logic"""
    # Initialize connection manager (for backward compatibility) and notification publisher
    connection_manager = get_connection_manager()
    notification_publisher = get_redis_publisher()

    try:
        # Step 1: Initialize dependencies

        # Publish task progress notification
        notification_publisher.publish(
            NotificationType.TASK_PROGRESS,
            {
                "task_id": task_id,
                "progress": 10.0,
                "message": "Initializing generation process..."
            }
        )

        # Get services needed for generation
        from app.application.dto.generation_dto import GenerationRequestDTO
        from app.application.services.generation_service import GenerationService
        from app.config import get_settings
        from app.infrastructure.ai.openai_provider import OpenAIProvider
        from app.infrastructure.image.stability_provider import StabilityProvider

        # Get application settings
        settings = get_settings()

        # Initialize storage and repositories using the centralized helper function
        storage, task_repo, webtoon_repo = _get_repositories()
        
        # Update task status to in-progress - use synchronous methods
        task = task_repo.get_by_id_sync(task_id) if hasattr(task_repo, 'get_by_id_sync') else await task_repo.get_by_id(task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(UTC)
            task.progress.current_operation = "Initializing generation process..."
            # Use synchronous save if available
            if hasattr(task_repo, 'save_sync'):
                task_repo.save_sync(task)
            else:
                await task_repo.save(task)

        # Initialize services directly without using dependency injection
        ai_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )

        image_generator = StabilityProvider(
            api_key=settings.stability_api_key,
            api_url=settings.stability_api_url,
        )

        generation_service = GenerationService(
            ai_provider=ai_provider,
            image_generator=image_generator,
            task_repository=task_repo,
            webtoon_repository=webtoon_repo,
        )

        # Convert request data to DTO
        request_data = request_data.copy()
        request_dto = GenerationRequestDTO(
            prompt=request_data["prompt"],
            art_style=request_data["art_style"],
            num_panels=request_data["num_panels"],
            character_descriptions=request_data.get("character_descriptions"),
            additional_context=request_data.get("additional_context"),
            style_preferences=request_data.get("style_preferences"),
        )

        # Step 2: Generate story
        await connection_manager.broadcast_generation_progress(
            task_id, 20.0, "Generating story structure..."
        )

        # Use helper function to ensure art_style is a valid string
        from app.domain.constants.art_styles import ensure_art_style_string
        art_style_str = ensure_art_style_string(request_dto.art_style)
        
        # Call AI provider methods directly with await
        story_data = await ai_provider.generate_story(
            request_dto.prompt,
            art_style_str,
            request_dto.additional_context,
        )

        # Step 3: Generate scenes
        await connection_manager.broadcast_generation_progress(
            task_id, 40.0, "Creating panel descriptions..."
        )

        scenes_data = await ai_provider.generate_scene_descriptions(
            story_data, request_dto.num_panels
        )

        # Step 4: Generate images
        total_panels = len(scenes_data)
        generated_panels = []

        for i, scene_data in enumerate(scenes_data):
            progress = 40.0 + (50.0 * (i + 1) / total_panels)
            # Publish task progress notification
            notification_publisher.publish(
                NotificationType.TASK_PROGRESS,
                {
                    "task_id": task_id,
                    "progress": progress,
                    "message": f"Generating image for panel {i + 1}/{total_panels}..."
                }
            )

            # Create enhanced prompt for image generation
            # We use the already converted art_style_str from earlier
            # No need to convert again
                
            enhanced_prompt = await ai_provider.enhance_visual_description(
                scene_data.get("visual_description", ""),
                art_style_str,
                {"style": art_style_str},
            )

            # Generate image - check availability and generate asynchronously
            if await image_generator.is_available():
                try:
                    (
                        local_path,
                        public_url,
                    ) = await image_generator.generate_image(
                        enhanced_prompt,
                        1024,
                        1024,
                        art_style_str,
                    )
                    scene_data["image_url"] = public_url
                except Exception as e:
                    logger.warning(f"Failed to generate image for panel {i}: {str(e)}")
                    scene_data["image_url"] = None
            else:
                scene_data["image_url"] = None

            generated_panels.append(scene_data)

            # Panel completion notification is handled through task progress

        # Step 5: Finalize webtoon
        await connection_manager.broadcast_generation_progress(
            task_id, 95.0, "Finalizing webtoon..."
        )

        # Get the existing webtoon_id from request_data, which was created as a placeholder
        webtoon_id = request_data.get("webtoon_id", None)
        
        # IMPORTANT: We must always have a webtoon_id at this point
        if not webtoon_id:
            # Fallback to creating a new ID if somehow no webtoon_id was provided
            webtoon_id = str(uuid4())
            logger.warning(f"No webtoon_id found in request data, creating new UUID: {webtoon_id}")
        else:
            logger.info(f"Using existing webtoon_id from request data: {webtoon_id}")
            
        # Ensure webtoon_id is a string
        if isinstance(webtoon_id, UUID):
            webtoon_id = str(webtoon_id)

        result = {
            "webtoon_id": webtoon_id,
            "title": story_data.get("title", "Generated Webtoon"),
            "panels": generated_panels,
            "story": story_data,
            "panel_count": len(generated_panels),
        }
        
        # Create an actual Webtoon entity and save it to the repository
        try:
            from app.domain.entities.webtoon import Webtoon
            from app.domain.entities.panel import Panel, SpeechBubble
            from app.domain.entities.scene import Scene
            from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
            from app.domain.value_objects.position import Position
            
            # We already have webtoon_repo initialized from _get_repositories() earlier in the function
            # No need to create a new WebtoonRepository instance
            
            # ALWAYS use the EXACT SAME ID that was passed in from the request_data
            # This ensures we update the placeholder webtoon created during API call
            webtoon_uuid = UUID(webtoon_id)
            logger.info(f"Attempting to fetch existing webtoon with ID: {webtoon_id}")
            
            # Fetch the existing webtoon using the repository from _get_repositories()
            try:
                # Use synchronous method if available, otherwise wrap async call
                if hasattr(webtoon_repo, 'get_by_id_sync'):
                    existing_webtoon = webtoon_repo.get_by_id_sync(webtoon_uuid)
                else:
                    existing_webtoon = await webtoon_repo.get_by_id(webtoon_uuid)
                    
                if existing_webtoon:
                    logger.info(f"Successfully found existing webtoon with ID {webtoon_id}, updating it")
                    webtoon = existing_webtoon
                    webtoon.title = story_data.get("title", "Generated Webtoon")
                    webtoon.description = story_data.get("description", "")
                    webtoon.art_style = art_style_str
                    # Clear existing panels if any (placeholder likely had none)
                    webtoon.panels = []
                else:
                    logger.warning(f"No existing webtoon found with ID {webtoon_id}, creating new webtoon")
                    # Create new webtoon with the SAME ID
                    webtoon = Webtoon(
                        id=webtoon_uuid,
                        title=story_data.get("title", "Generated Webtoon"),
                        description=story_data.get("description", ""),
                        art_style=art_style_str
                    )
            except Exception as e:
                # Log the error but don't swallow it - we need to know if something is wrong
                # with our storage layer
                logger.error(f"Error fetching webtoon with ID {webtoon_id}: {str(e)}")
                raise Exception(f"Failed to fetch or create webtoon with ID {webtoon_id}: {str(e)}")
            
            # Create and add panels to the webtoon
            for i, panel_data in enumerate(generated_panels):
                # Create scene object
                scene = Scene(
                    description=panel_data.get("visual_description", ""),
                    setting=panel_data.get("setting", ""),
                    time_of_day="day",  # Default values
                    weather="clear",
                    mood=panel_data.get("mood", ""),
                    character_names=panel_data.get("characters", []),
                    camera_angle=panel_data.get("camera_angle", "medium"),
                    character_positions={},
                    character_expressions={},
                    actions=[],
                    lighting="natural",
                    composition_notes=""
                )
                
                # Create panel with scene
                panel = Panel(
                    sequence_number=i + 1,
                    scene=scene,
                    dimensions=PanelDimensions(size=PanelSize.FULL),
                    image_url=panel_data.get("image_url", "")
                )
                
                # Add speech bubbles if they exist
                dialogue = panel_data.get("dialogue", [])
                for j, dialogue_item in enumerate(dialogue):
                    if isinstance(dialogue_item, dict) and "character" in dialogue_item and "text" in dialogue_item:
                        bubble = SpeechBubble(
                            character_name=dialogue_item["character"],
                            text=dialogue_item["text"],
                            position=Position(x_percent=50, y_percent=50, anchor="center")
                        )
                        panel.speech_bubbles.append(bubble)
                
                # Add special effects if they exist
                panel.visual_effects = panel_data.get("special_effects", [])
                
                # Add panel to webtoon
                webtoon.add_panel(panel)
            
            # We already initialized the webtoon_repository above
            # No need to initialize it again
            
            # Save the webtoon entity to storage using the centralized repository
            if hasattr(webtoon_repo, 'save_sync'):
                webtoon_repo.save_sync(webtoon)
            else:
                await webtoon_repo.save(webtoon)
            logger.info(f"Saved webtoon entity to repository with ID: {webtoon_id} and {len(webtoon.panels)} panels")
        except Exception as webtoon_save_error:
            logger.error(f"Failed to save webtoon entity: {str(webtoon_save_error)}", exc_info=True)

        # Step 6: Complete
        # Publish final progress notification
        notification_publisher.publish(
            NotificationType.TASK_PROGRESS,
            {
                "task_id": task_id,
                "progress": 100.0,
                "message": "Generation completed!"
            }
        )

        # Update task status in the database
        # Use centralized repository initialization 
        storage, task_repository, webtoon_repo = _get_repositories()
        # Use synchronous method if available, otherwise wrap async call
        if hasattr(task_repository, 'get_by_id_sync'):
            task = task_repository.get_by_id_sync(task_id)
        else:
            task = await task_repository.get_by_id(task_id)
            
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(UTC)
            task.result = result
            task.progress.current_step = task.progress.total_steps
            task.progress.percentage = 100.0
            task.progress.current_operation = "Generation completed!"
            
            # Use synchronous save method if available
            if hasattr(task_repository, 'save_sync'):
                task_repository.save_sync(task)
            else:
                await task_repository.save(task)

        # Publish task completion notification
        notification_publisher.publish(
            NotificationType.TASK_COMPLETED,
            {
                "task_id": task_id,
                "result": result,
                "webtoon_id": webtoon_id
            }
        )
        
        # Fetch and broadcast HTML content
        try:
            # Import the webtoon service and renderer
            from app.application.services.webtoon_service import WebtoonService
            from app.utils.webtoon_renderer import WebtoonRenderer
            
            # We already have webtoon_repo initialized from _get_repositories()
            # Just use that instance for the webtoon service
            renderer = WebtoonRenderer()
            webtoon_service = WebtoonService(webtoon_repo, renderer)
            
            # Fetch HTML content - directly await the function call
            html_content = await webtoon_service.get_webtoon_html_content(UUID(webtoon_id))
            
            # Publish webtoon update notification if HTML content is available
            if html_content:
                logger.info(f"Publishing webtoon update notification for: {webtoon_id} with task_id: {task_id}")
                notification_publisher.publish(
                    NotificationType.WEBTOON_UPDATED,
                    {
                        "task_id": task_id,
                        "webtoon_id": webtoon_id,
                        "html_content": html_content
                    }
                )
        except Exception as html_error:
            logger.error(f"Error fetching/broadcasting HTML content: {str(html_error)}", exc_info=True)

        logger.info(f"Webtoon generation completed: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Error in async generation {task_id}: {str(e)}")
        
        # Update task status in the database using centralized repository initialization
        _, task_repository, _ = _get_repositories()
        task = await task_repository.get_by_id(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(UTC)
            task.error_message = str(e)
            await task_repository.save(task)


async def notify_generation_failed(task_id: str, error_message: str):
    """Notify WebSocket clients about generation failure via Redis"""
    try:
        notification_publisher = get_redis_publisher()
        notification_publisher.publish(
            NotificationType.TASK_FAILED,
            {
                "task_id": task_id,
                "error": error_message
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error publishing failure notification: {str(e)}")
        return False


@celery_app.task
def cleanup_old_tasks():
    """Periodic task to clean up old completed tasks"""
    logger.info("Running task cleanup...")
    # Implement cleanup logic
    return "Cleanup completed"


@celery_app.task(bind=True)
def start_panel_generation_task(self, task_id: str, request_data: Dict[str, Any]):
    """Background task for single panel generation"""
    task_name = self.name
    task_id_celery = self.request.id
    task_retries = self.request.retries
    
    # Log environment info to debug API key issues
    logger.info(f"Panel generation task started. Task ID: {task_id}")
    
    # Access settings via Celery app configuration
    stability_api_key = celery_app.conf.get('STABILITY_API_KEY') or os.environ.get('STABILITY_API_KEY')
    logger.info(f"STABILITY_API_KEY available: {stability_api_key is not None}")
    if stability_api_key:
        logger.info(f"API key length: {len(stability_api_key)}")
    else:
        logger.warning("STABILITY_API_KEY is None or empty!")
    
    # Ensure art_style is a string if present
    if 'art_style' in request_data:
        from app.domain.constants.art_styles import ensure_art_style_string
        request_data['art_style'] = ensure_art_style_string(request_data['art_style'])
    
    logger.info(f"Starting panel generation task {task_id} (celery ID: {task_id_celery})")
    
    # Initialize storage and repositories using the centralized helper function
    try:
        # Use the centralized repository initialization
        storage, task_repo, webtoon_repo = _get_repositories()
        
        # Check if task exists in storage before updating
        # Use asyncio.run to execute the coroutine in a sync context
        task = asyncio.run(task_repo.get_by_id(task_id))
        if not task:
            logger.warning(f"Task {task_id} not found in storage. Creating task record.")
            from app.domain.entities.generation_task import GenerationTask, TaskType, TaskProgress
            task = GenerationTask(
                id=task_id,
                task_type=TaskType.PANEL_GENERATION,
                status=TaskStatus.PENDING,
                input_data=request_data,
                created_at=datetime.now(UTC),
                progress=TaskProgress()
            )
        
        # Update task status to processing
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(UTC)
        
        # Save the updated task
        asyncio.run(task_repo.save(task))
        
        # Get websocket connection manager
        connection_manager = get_connection_manager()
        
        # Notify clients that processing has started
        asyncio.run(connection_manager.broadcast_generation_progress(
            task_id, 0.0, "Starting panel generation..."
        ))
        
        # Run the async generation logic in a synchronous context
        try:
            result = asyncio.run(generate_panel_async(task_id, request_data))
            
            # Update task with completion info
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(UTC)
            task.result = result
            task.progress.percentage = 100.0
            task.progress.current_step = task.progress.total_steps
            task.progress.current_operation = "Panel generation completed successfully"
            
            # Save the completed task
            asyncio.run(task_repo.save(task))
            
            # Notify WebSocket clients of completion
            logger.info(f"Broadcasting panel generation completion: {task_id}")
            asyncio.run(connection_manager.broadcast_generation_completed(
                task_id, result
            ))
            
            # Fetch and broadcast HTML content if we have a webtoon_id
            if 'webtoon_id' in request_data:
                try:
                    webtoon_id = request_data['webtoon_id']
                    
                    # Import the webtoon service
                    from app.application.services.webtoon_service import WebtoonService, get_webtoon_service
                    
                    # Get webtoon service
                    webtoon_service = get_webtoon_service()
                    
                    # Fetch HTML content asynchronously
                    html_content = asyncio.run(webtoon_service.get_webtoon_html_content(UUID(webtoon_id)))
                    
                    # Broadcast update if HTML content is available
                    if html_content:
                        logger.info(f"Broadcasting HTML update for webtoon: {webtoon_id}")
                        asyncio.run(connection_manager.broadcast_webtoon_updated(webtoon_id, html_content))
                except Exception as html_error:
                    logger.error(f"Error fetching/broadcasting HTML content: {str(html_error)}", exc_info=True)
            
            # Return the result for Celery task tracking
            return result
            
        except Exception as e:
            # Handle errors in panel generation
            logger.error(f"Panel generation failed: {str(e)}", exc_info=True)
            
            # Update task with failure info
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(UTC)
            
            # Save the failed task
            asyncio.run(task_repo.save(task))
            
            # Notify clients of failure
            asyncio.run(notify_generation_failed(task_id, str(e)))
            # Re-raise the exception for Celery to handle
            raise
            
    except Exception as e:
        logger.error(f"Error in panel generation task: {str(e)}", exc_info=True)
        # Notify clients of failure through WebSocket
        try:
            connection_manager = get_connection_manager()
            asyncio.run(notify_generation_failed(task_id, str(e)))
        except Exception as notify_error:
            logger.error(f"Failed to notify clients of error: {str(notify_error)}")
        # Re-raise the exception for Celery to handle
        raise


def generate_webtoon_sync(task_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous version of webtoon generation logic for Celery tasks"""
    # We'll still use the async connection manager for WebSockets, but through asyncio.run
    logger.info(f"Starting synchronous webtoon generation for task: {task_id}")
    
    connection_manager = get_connection_manager()
    
    # Initialize repositories and services
    try:
        # Get settings for storage and other configurations
        from app.config import get_settings
        settings = get_settings()
        
        # Initialize storage
        from app.infrastructure.storage.file_storage import FileStorage
        storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "/app/storage"))
        storage = FileStorage(storage_path)
        task_repository = TaskRepository(storage)
        
        # Get connection manager
        connection_manager = get_connection_manager()
        
        # Initialize AI provider with required API key
        from app.infrastructure.ai.openai_provider import OpenAIProvider
        ai_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )
        
        # Initialize image generator with required API key
        from app.infrastructure.image.stability_provider import StabilityProvider
        image_generator = StabilityProvider(
            api_key=settings.stability_api_key,
            api_url=settings.stability_api_url,
        )
        
        # Extract parameters from request data
        scene_description = request_data.get("scene_description")
        art_style = request_data.get("art_style")
        character_names = request_data.get("character_names", [])
        panel_size = request_data.get("panel_size", "full")
        mood = request_data.get("mood")
        prompt = request_data.get("prompt")
        style_preferences = request_data.get("style_preferences", {})
        
        # Notify clients of panel detail generation
        asyncio.run(connection_manager.broadcast_generation_progress(
            task_id, 20.0, "Generating panel details..."
        ))
        
        # Generate panel details using combination of existing methods
        panel_details = {}
        
        # Generate dialogue using available method if we have character names
        if character_names:
            try:
                dialogue = asyncio.run(ai_provider.generate_dialogue(
                    scene_description=scene_description,
                    character_names=character_names,
                    mood=mood or "neutral"
                ))
                panel_details["dialogue"] = dialogue
            except Exception as e:
                logger.warning(f"Failed to generate dialogue: {str(e)}")
                panel_details["dialogue"] = []
        
        # Enhance the visual description for better image generation
        try:
            # Create technical specifications for visual enhancement
            tech_specs = {
                "panel_size": panel_size,
                "mood": mood or "neutral",
                "style_preferences": style_preferences or {}
            }
            
            enhanced_description = asyncio.run(ai_provider.enhance_visual_description(
                base_description=scene_description,
                art_style=art_style,
                technical_specs=tech_specs
            ))
            panel_details["visual_description"] = enhanced_description
        except Exception as e:
            logger.warning(f"Failed to enhance visual description: {str(e)}")
            panel_details["visual_description"] = scene_description
        
        # Update progress
        asyncio.run(connection_manager.broadcast_generation_progress(
            task_id, 50.0, "Generating panel image..."
        ))
        
        # Generate image for the panel
        image_url = None
        try:
            # Create enhanced prompt for image generation using centralized prompt templates
            visual_description = panel_details.get("visual_description", scene_description)
            prompt_templates = PromptTemplates()
            enhanced_prompt = prompt_templates.format_image_generation_prompt(
                visual_description=visual_description,
                art_style=art_style,
                style_preferences=style_preferences
            )
                
            # Generate the image
            image_result = asyncio.run(image_generator.generate_image(
                prompt=enhanced_prompt,
                style=art_style,  # Using the correct parameter name 'style' instead of 'art_style'
                width=1024,  # Default width, can be adjusted based on panel_size
                height=768   # Default height, can be adjusted based on panel_size
            ))
            
            # StabilityProvider.generate_image returns a tuple of (file_path, public_url)
            if image_result and len(image_result) == 2:
                file_path, public_url = image_result
                image_url = public_url
                panel_details["image_url"] = image_url
                logger.info(f"Generated image saved at {file_path}, public URL: {public_url}")
            else:
                logger.warning("Image generation did not return the expected tuple format")
        except Exception as e:
            logger.warning(f"Failed to generate image for panel: {str(e)}")
            panel_details["image_url"] = None
        
        # Notify clients of panel completion
        asyncio.run(connection_manager.broadcast_generation_progress(
            task_id, 100.0, "Panel generation completed!"
        ))
        
        # Prepare the result data
        result = {
            "panel": panel_details,
            "image_url": image_url
        }
        
        # Notify panel completion
        asyncio.run(connection_manager.broadcast_task_update(
            task_id,
            {
                "panel_generated": {
                    "panel_details": panel_details,
                    "image_url": image_url
                }
            },
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error in async panel generation: {str(e)}", exc_info=True)
        # Initialize storage and repository if not already done
        if not storage:
            from app.infrastructure.storage.file_storage import FileStorage
            from app.config import get_settings
            settings = get_settings()
            storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "/app/storage"))
            storage = FileStorage(storage_path)
        if not task_repository:
            task_repository = TaskRepository(storage)
        
        # Get the task and update its status
        task = task_repository.get_by_id_sync(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task_repository.save_sync(task)
        
        # Re-raise the exception
        raise
