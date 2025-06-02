# app/tasks/generation_tasks.py
"""
Background tasks for webtoon generation
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from celery import current_task

from app.tasks.celery_app import celery_app
from app.websocket.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def start_webtoon_generation_task(self, task_id: str, request_data: Dict[str, Any]):
    """Background task for webtoon generation"""
    logger.info(f"Starting webtoon generation task: {task_id}")

    try:
        # Run the async generation in sync context
        result = asyncio.run(generate_webtoon_async(task_id, request_data))
        return result
    except Exception as e:
        logger.error(f"Error in webtoon generation task {task_id}: {str(e)}")
        # Notify WebSocket clients of failure
        asyncio.run(notify_generation_failed(task_id, str(e)))
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
        from app.domain.value_objects.style import ArtStyle
        from app.infrastructure.ai.openai_provider import OpenAIProvider
        from app.infrastructure.image.stability_provider import StabilityProvider
        from app.infrastructure.storage.memory_storage import MemoryStorage

        # Get settings
        settings = get_settings()

        # Initialize storage and repositories
        storage = MemoryStorage()
        webtoon_repo = WebtoonRepository(storage)
        task_repo = TaskRepository(storage)

        # Initialize services directly without using dependency injection
        ai_provider = OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )

        image_generator = StabilityProvider(
            api_key=settings.stability_api_key, api_url=settings.stability_api_url
        )

        generation_service = GenerationService(
            ai_provider=ai_provider,
            image_generator=image_generator,
            task_repository=task_repo,
            webtoon_repository=webtoon_repo,
        )

        # Convert request data to DTO
        request_dto = GenerationRequestDTO(
            prompt=request_data["prompt"],
            art_style=ArtStyle(request_data["art_style"]),
            num_panels=request_data["num_panels"],
            character_descriptions=request_data.get("character_descriptions"),
            additional_context=request_data.get("additional_context"),
            style_preferences=request_data.get("style_preferences"),
        )

        # Step 2: Generate story
        await connection_manager.broadcast_generation_progress(
            task_id, 20.0, "Generating story structure..."
        )

        story_data = await ai_provider.generate_story(
            request_dto.prompt,
            request_dto.art_style.value,
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
            enhanced_prompt = await ai_provider.enhance_visual_description(
                scene_data.get("visual_description", ""),
                request_dto.art_style.value,
                {"style": request_dto.art_style.value},
            )

            # Generate image
            if image_generator.is_available():
                try:
                    local_path, public_url = await image_generator.generate_image(
                        enhanced_prompt, 1024, 1024, request_dto.art_style.value
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

        await connection_manager.broadcast_generation_completed(
            task_id, webtoon_id, result
        )

        logger.info(f"Webtoon generation completed: {task_id}")
        return result

    except Exception as e:
        logger.error(f"Error in async generation {task_id}: {str(e)}")
        await connection_manager.broadcast_generation_failed(task_id, str(e))
        raise


async def notify_generation_failed(task_id: str, error_message: str):
    """Notify WebSocket clients of generation failure"""
    connection_manager = get_connection_manager()
    await connection_manager.broadcast_generation_failed(task_id, error_message)


@celery_app.task
def cleanup_old_tasks():
    """Periodic task to clean up old completed tasks"""
    logger.info("Running task cleanup...")
    # Implement cleanup logic
    return "Cleanup completed"
