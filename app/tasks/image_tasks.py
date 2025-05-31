# =============================================================================
# app/tasks/image_tasks.py
# =============================================================================
import asyncio
import logging
from typing import Any, Dict, List

from celery import current_task

from app.core.celery_app import celery_app
from app.core.config import settings
from app.domain.models.task import TaskStatus
from app.infrastructure.ai import OpenAIClient, PanelProcessor, StabilityAIGenerator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="generate_panel_image")
def generate_panel_image(
    self,
    user_id: str,
    visual_prompt: str,
    style: str = "webtoon",
    quality: str = "standard",
    width: int = 1024,
    height: int = 1024,
) -> Dict[str, Any]:
    """Generate panel image from visual prompt."""
    try:
        self.update_state(
            state=TaskStatus.RUNNING.value,
            meta={"progress": 10, "current_step": "Initializing image generation"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Initialize AI clients
            llm_client = OpenAIClient(
                api_key=settings.openai_api_key, model=settings.default_llm_model
            )

            image_generator = StabilityAIGenerator(api_key=settings.stability_ai_api_key)

            panel_processor = PanelProcessor(llm_client, image_generator)

            # Generate image
            self.update_state(
                state=TaskStatus.RUNNING.value,
                meta={"progress": 50, "current_step": "Generating image"},
            )

            result = loop.run_until_complete(
                panel_processor.generate_panel_image(visual_prompt, style, quality, width, height)
            )

            self.update_state(
                state=TaskStatus.COMPLETED.value,
                meta={"progress": 100, "current_step": "Completed", "result": result},
            )

            return result

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise


@celery_app.task(bind=True, name="generate_visual_prompt")
def generate_visual_prompt(
    self,
    user_id: str,
    scene_description: Dict[str, Any],
    characters: List[Dict[str, Any]],
    style: str = "webtoon",
) -> str:
    """Generate visual prompt for image generation."""
    try:
        self.update_state(
            state=TaskStatus.RUNNING.value, meta={"progress": 10, "current_step": "Analyzing scene"}
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Initialize AI clients
            llm_client = OpenAIClient(
                api_key=settings.openai_api_key, model=settings.default_llm_model
            )

            image_generator = StabilityAIGenerator(api_key=settings.stability_ai_api_key)

            panel_processor = PanelProcessor(llm_client, image_generator)

            # Generate visual prompt
            self.update_state(
                state=TaskStatus.RUNNING.value,
                meta={"progress": 50, "current_step": "Creating visual prompt"},
            )

            result = loop.run_until_complete(
                panel_processor.generate_visual_prompt(scene_description, characters, style)
            )

            self.update_state(
                state=TaskStatus.COMPLETED.value,
                meta={"progress": 100, "current_step": "Completed", "result": result},
            )

            return result

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Visual prompt generation failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise
