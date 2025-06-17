# app/tasks/generation_tasks.py
"""
Background tasks for webtoon generation
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timezone, UTC
from typing import Any, Dict, List
from uuid import UUID

from app.tasks.celery_app import celery_app
from app.websocket.connection_manager import get_connection_manager
from app.domain.entities.generation_task import TaskStatus
from app.domain.repositories.task_repository import TaskRepository
from app.application.interfaces.storage_provider import StorageProvider

# Configure root logger to see all debug messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def start_webtoon_generation_task(self, task_id: str, request_data: Dict[str, Any]):
    """Background task for webtoon generation"""
    task_name = self.name
    task_id_celery = self.request.id
    task_retries = self.request.retries
    
    # Log detailed information about the art_style field
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
    
    logger.debug(f"CELERY TASK EXECUTION START - Task {task_name} with request ID {task_id_celery}")
    logger.debug(f"Task parameters - task_id: {task_id}")
    logger.debug(f"Request data keys: {list(request_data.keys())}")
    if 'art_style' in request_data:
        logger.debug(f"art_style after processing: {request_data['art_style']} (type: {type(request_data['art_style']).__name__})")
    logger.debug(f"Environment variables: REDIS_URL={os.environ.get('REDIS_URL')}, CELERY_BROKER_URL={os.environ.get('CELERY_BROKER_URL')}")
    
    # Initialize storage directly here for consistent file storage usage
    try:
        logger.debug("Getting settings for storage initialization")
        # Get settings
        from app.config import get_settings
        settings = get_settings()
        
        # Initialize storage with proper settings for Docker environment
        # Force file storage for consistency
        from app.infrastructure.storage.file_storage import FileStorage
        
        # Handle both standard and Docker settings paths
        storage_type = getattr(settings, "storage_type", getattr(settings, "storage_provider", "file"))        
        storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "/app/storage"))
        
        # Log the storage configuration for debugging
        logger.debug(f"Using storage type: {storage_type} at path: {storage_path}")
        
        # List storage directory contents to verify access
        try:
            if os.path.exists(storage_path):
                files = os.listdir(storage_path)
                logger.debug(f"Storage directory exists. Contents: {files[:10] if len(files) > 10 else files}")
            else:
                logger.warning(f"Storage directory {storage_path} does not exist")
                os.makedirs(storage_path, exist_ok=True)
                logger.debug(f"Created storage directory {storage_path}")
        except Exception as e:
            logger.error(f"Error accessing storage directory: {str(e)}")
        
        # Always use file storage in the Celery task for consistency with API
        logger.debug("Initializing file storage and task repository")
        storage = FileStorage(storage_path)
        task_repo = TaskRepository(storage)
        
        # Check if task exists in storage before updating
        # Use asyncio.run to execute the coroutine in a sync context
        task = asyncio.run(task_repo.get_by_id(task_id))
        if not task:
            logger.warning(f"Task {task_id} not found in storage. Creating task record.")
            from app.domain.entities.generation_task import GenerationTask, TaskType, TaskProgress
            task = GenerationTask(
                id=task_id,
                task_type=TaskType.WEBTOON_GENERATION,
                status=TaskStatus.PENDING,
                input_data=request_data,
                created_at=datetime.now(timezone.utc),
                progress=TaskProgress()
            )
        
        # Update task status to IN_PROGRESS before starting
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)
        # Use asyncio.run to execute the coroutine in a sync context
        asyncio.run(task_repo.save(task))
        logger.debug(f"Updated task {task_id} status to IN_PROGRESS")
        
        # Run the async generation in sync context
        logger.debug(f"Starting async generation for task {task_id}")
        result = asyncio.run(generate_webtoon_async(task_id, request_data))
        logger.debug(f"Async generation completed for task {task_id}")
        
        # Double-check that task status is updated to COMPLETED
        task = asyncio.run(task_repo.get_by_id(task_id))
        if task and task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
            asyncio.run(task_repo.save(task))
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
            
            # Use asyncio.run to execute async methods in a sync context
            task = asyncio.run(task_repo.get_by_id(task_id))
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now(timezone.utc)
                # Use asyncio.run to execute async save method
                asyncio.run(task_repo.save(task))
                logger.debug(f"Updated task {task_id} status to FAILED")
        except Exception as inner_e:
            logger.error(f"Failed to update task status to FAILED: {str(inner_e)}", exc_info=True)
            
        # Notify WebSocket clients of failure
        try:
            asyncio.run(notify_generation_failed(task_id, str(e)))
        except Exception as ws_error:
            logger.error(f"Failed to send WebSocket notification: {str(ws_error)}")
            
        raise


async def generate_webtoon_async(
    task_id: str, request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Async webtoon generation logic"""
    connection_manager = get_connection_manager()

    try:
        # Step 1: Initialize dependencies
        await connection_manager.broadcast_generation_progress(
            task_id, 10.0, "Initializing generation process..."
        )

        # Get services (in real implementation, properly initialize these)
        from app.application.dto.generation_dto import GenerationRequestDTO
        from app.application.services.generation_service import GenerationService
        from app.config import get_settings
        from app.domain.repositories.task_repository import TaskRepository
        from app.domain.repositories.webtoon_repository import WebtoonRepository
        # TaskStatus is already imported at the top-level
        from app.application.interfaces.storage_provider import StorageProvider
        from app.infrastructure.ai.openai_provider import OpenAIProvider
        from app.infrastructure.image.stability_provider import StabilityProvider
        from app.infrastructure.storage.file_storage import FileStorage

        # Get settings
        settings = get_settings()

        # Initialize storage and repositories based on settings
        # Handle both storage_type (standard config) and storage_provider (docker settings)
        storage_type = getattr(settings, "storage_type", getattr(settings, "storage_provider", "memory"))
        if storage_type == "file":
            # Handle both file_storage_path (standard config) and storage_path (docker settings)
            storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "./storage"))
            storage = FileStorage(storage_path)
        else:
            from app.infrastructure.storage.memory_storage import MemoryStorage
            storage = MemoryStorage()            
        webtoon_repo = WebtoonRepository(storage)
        task_repo = TaskRepository(storage)
        
        # Update task status to in-progress
        task = await task_repo.get_by_id(task_id)
        if task:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(UTC)
            task.progress.current_operation = "Initializing generation process..."
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
            await connection_manager.broadcast_generation_progress(
                task_id,
                progress,
                f"Generating image for panel {i + 1}/{total_panels}...",
            )

            # Create enhanced prompt for image generation
            # We use the already converted art_style_str from earlier
            # No need to convert again
                
            enhanced_prompt = await ai_provider.enhance_visual_description(
                scene_data.get("visual_description", ""),
                art_style_str,
                {"style": art_style_str},
            )

            # Generate image
            if image_generator.is_available():
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

            # Notify panel completion
            await connection_manager.broadcast_task_update(
                task_id,
                {
                    "panel_generated": {
                        "panel_number": i + 1,
                        "total_panels": total_panels,
                        "image_url": scene_data.get("image_url"),
                    }
                },
            )

        # Step 5: Finalize webtoon
        await connection_manager.broadcast_generation_progress(
            task_id, 95.0, "Finalizing webtoon..."
        )

        # Create webtoon entity and save (simplified for this example)
        webtoon_id = str(UUID(int=0))  # Generate proper UUID in real implementation

        result = {
            "webtoon_id": webtoon_id,
            "title": story_data.get("title", "Generated Webtoon"),
            "panels": generated_panels,
            "story": story_data,
            "panel_count": len(generated_panels),
        }

        # Step 6: Complete
        await connection_manager.broadcast_generation_progress(
            task_id, 100.0, "Generation completed!"
        )

        # Update task status in the database
        # Initialize storage similar to how it's done in the exception handler
        storage_type = getattr(settings, "storage_type", getattr(settings, "storage_provider", "memory"))
        if storage_type == "file":
            storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "./storage"))
            from app.infrastructure.storage.file_storage import FileStorage
            storage = FileStorage(storage_path)
        else:
            from app.infrastructure.storage.memory_storage import MemoryStorage
            storage = MemoryStorage()
        
        task_repository = TaskRepository(storage)
        task = await task_repository.get_by_id(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(UTC)
            task.result = result
            task.progress.current_step = task.progress.total_steps
            task.progress.percentage = 100.0
            task.progress.current_operation = "Generation completed!"
            await task_repository.save(task)

        await connection_manager.broadcast_generation_completed(
            task_id, webtoon_id, result
        )

        logger.info(f"Webtoon generation completed: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Error in async generation {task_id}: {str(e)}")
        
        # Update task status in the database for failures
        # Initialize storage similar to the main function body
        storage_type = getattr(settings, "storage_type", getattr(settings, "storage_provider", "memory"))
        if storage_type == "file":
            storage_path = getattr(settings, "file_storage_path", getattr(settings, "storage_path", "./storage"))
            from app.infrastructure.storage.file_storage import FileStorage
            error_storage = FileStorage(storage_path)
        else:
            from app.infrastructure.storage.memory_storage import MemoryStorage
            error_storage = MemoryStorage()
        
        task_repository = TaskRepository(error_storage)
        task = await task_repository.get_by_id(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(UTC)
            task.error_message = str(e)
            await task_repository.save(task)
            
        await connection_manager.broadcast_generation_failed(task_id, str(e))
        raise


async def notify_generation_failed(task_id: str, error_message: str):
    """Notify WebSocket clients of generation failure"""
    logger.debug(f"Sending failure notification for task {task_id}: {error_message}")
    connection_manager = get_connection_manager()
    await connection_manager.broadcast_generation_failed(task_id, error_message)


@celery_app.task
def cleanup_old_tasks():
    """Periodic task to clean up old completed tasks"""
    logger.info("Running task cleanup...")
    # Implement cleanup logic
    return "Cleanup completed"
