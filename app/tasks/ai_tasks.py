# =============================================================================
# app/tasks/ai_tasks.py
# =============================================================================
import asyncio
import logging
from typing import Any, Dict, List

from celery import current_task

from app.core.celery_app import celery_app
from app.core.config import settings
from app.domain.models.task import TaskStatus
from app.infrastructure.ai import OpenAIClient, StoryProcessor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="generate_story_outline")
def generate_story_outline(
    self, user_id: str, story_prompt: str, style: str = "webtoon", target_panels: int = 6
) -> Dict[str, Any]:
    """Generate story outline from prompt."""
    try:
        self.update_state(
            state=TaskStatus.RUNNING.value,
            meta={"progress": 10, "current_step": "Analyzing story prompt"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Initialize AI client
            llm_client = OpenAIClient(
                api_key=settings.openai_api_key, model=settings.default_llm_model
            )

            story_processor = StoryProcessor(llm_client)

            # Generate story outline
            self.update_state(
                state=TaskStatus.RUNNING.value,
                meta={"progress": 50, "current_step": "Generating story outline"},
            )

            result = loop.run_until_complete(
                story_processor.generate_story_outline(story_prompt, style, target_panels)
            )

            self.update_state(
                state=TaskStatus.COMPLETED.value,
                meta={"progress": 100, "current_step": "Completed", "result": result},
            )

            return result

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Story outline generation failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise


@celery_app.task(bind=True, name="expand_characters")
def expand_characters(self, user_id: str, characters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Expand character descriptions."""
    try:
        self.update_state(
            state=TaskStatus.RUNNING.value,
            meta={"progress": 10, "current_step": "Initializing character expansion"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Initialize AI client
            llm_client = OpenAIClient(
                api_key=settings.openai_api_key, model=settings.default_llm_model
            )

            story_processor = StoryProcessor(llm_client)

            # Expand characters
            self.update_state(
                state=TaskStatus.RUNNING.value,
                meta={"progress": 50, "current_step": "Expanding character details"},
            )

            result = loop.run_until_complete(story_processor.expand_characters(characters))

            self.update_state(
                state=TaskStatus.COMPLETED.value,
                meta={"progress": 100, "current_step": "Completed", "result": result},
            )

            return result

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Character expansion failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise


@celery_app.task(bind=True, name="generate_scene_descriptions")
def generate_scene_descriptions(
    self, user_id: str, story_outline: Dict[str, Any], target_panels: int
) -> List[Dict[str, Any]]:
    """Generate scene descriptions for panels."""
    try:
        self.update_state(
            state=TaskStatus.RUNNING.value,
            meta={"progress": 10, "current_step": "Analyzing story structure"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Initialize AI client
            llm_client = OpenAIClient(
                api_key=settings.openai_api_key, model=settings.default_llm_model
            )

            story_processor = StoryProcessor(llm_client)

            # Generate scenes
            self.update_state(
                state=TaskStatus.RUNNING.value,
                meta={"progress": 50, "current_step": "Creating scene descriptions"},
            )

            result = loop.run_until_complete(
                story_processor.generate_scene_descriptions(story_outline, target_panels)
            )

            self.update_state(
                state=TaskStatus.COMPLETED.value,
                meta={"progress": 100, "current_step": "Completed", "result": result},
            )

            return result

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Scene description generation failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise
