# =============================================================================
# app/tasks/webtoon_tasks.py
# =============================================================================
import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from celery import current_task

from app.core.celery_app import celery_app
from app.core.config import settings
from app.domain.models.task import TaskStatus, TaskType
from app.infrastructure.ai import OpenAIClient, PanelProcessor, StabilityAIGenerator, StoryProcessor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="generate_complete_webtoon")
def generate_complete_webtoon(
    self,
    user_id: str,
    project_id: str,
    story_prompt: str,
    style: str = "webtoon",
    panel_count: int = 6,
    quality: str = "standard",
) -> Dict[str, Any]:
    """Generate a complete webtoon from story prompt."""
    try:
        # Update task status
        self.update_state(
            state=TaskStatus.RUNNING.value,
            meta={"progress": 0, "current_step": "Initializing webtoon generation"},
        )

        # Run async workflow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                _generate_webtoon_workflow(
                    self, user_id, project_id, story_prompt, style, panel_count, quality
                )
            )
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Webtoon generation failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise


async def _generate_webtoon_workflow(
    task,
    user_id: str,
    project_id: str,
    story_prompt: str,
    style: str,
    panel_count: int,
    quality: str,
) -> Dict[str, Any]:
    """Async workflow for webtoon generation."""

    # Initialize AI clients
    llm_client = OpenAIClient(api_key=settings.openai_api_key, model=settings.default_llm_model)

    image_generator = StabilityAIGenerator(api_key=settings.stability_ai_api_key)

    story_processor = StoryProcessor(llm_client)
    panel_processor = PanelProcessor(llm_client, image_generator)

    # Step 1: Generate story outline (20% progress)
    task.update_state(
        state=TaskStatus.RUNNING.value,
        meta={"progress": 10, "current_step": "Generating story outline"},
    )

    story_outline = await story_processor.generate_story_outline(story_prompt, style, panel_count)

    # Step 2: Expand characters (40% progress)
    task.update_state(
        state=TaskStatus.RUNNING.value,
        meta={"progress": 20, "current_step": "Developing characters"},
    )

    expanded_characters = await story_processor.expand_characters(story_outline["characters"])

    # Step 3: Generate scene descriptions (60% progress)
    task.update_state(
        state=TaskStatus.RUNNING.value,
        meta={"progress": 40, "current_step": "Creating scene descriptions"},
    )

    scenes = await story_processor.generate_scene_descriptions(story_outline, panel_count)

    # Step 4: Generate panel images (80% progress)
    task.update_state(
        state=TaskStatus.RUNNING.value,
        meta={"progress": 60, "current_step": "Generating panel images"},
    )

    panels = []
    for i, scene in enumerate(scenes):
        panel_progress = 60 + (20 * (i + 1) / len(scenes))
        task.update_state(
            state=TaskStatus.RUNNING.value,
            meta={
                "progress": panel_progress,
                "current_step": f"Generating panel {i + 1} of {len(scenes)}",
            },
        )

        panel_result = await panel_processor.generate_complete_panel(
            scene, expanded_characters, style, quality
        )

        panels.append(panel_result)

    # Step 5: Finalize webtoon (100% progress)
    task.update_state(
        state=TaskStatus.RUNNING.value, meta={"progress": 90, "current_step": "Finalizing webtoon"}
    )

    webtoon_data = {
        "story_outline": story_outline,
        "characters": expanded_characters,
        "scenes": scenes,
        "panels": panels,
        "metadata": {
            "style": style,
            "panel_count": len(panels),
            "quality": quality,
            "generation_time": task.request.eta,
        },
    }

    task.update_state(
        state=TaskStatus.COMPLETED.value,
        meta={"progress": 100, "current_step": "Completed", "result": webtoon_data},
    )

    return webtoon_data


@celery_app.task(bind=True, name="generate_single_panel")
def generate_single_panel(
    self,
    user_id: str,
    webtoon_id: str,
    scene_description: Dict[str, Any],
    characters: List[Dict[str, Any]],
    style: str = "webtoon",
    quality: str = "standard",
) -> Dict[str, Any]:
    """Generate a single panel."""
    try:
        self.update_state(
            state=TaskStatus.RUNNING.value,
            meta={"progress": 0, "current_step": "Initializing panel generation"},
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                _generate_single_panel_workflow(self, scene_description, characters, style, quality)
            )
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Panel generation failed: {str(e)}")
        self.update_state(state=TaskStatus.FAILED.value, meta={"error": str(e), "progress": 0})
        raise


async def _generate_single_panel_workflow(
    task,
    scene_description: Dict[str, Any],
    characters: List[Dict[str, Any]],
    style: str,
    quality: str,
) -> Dict[str, Any]:
    """Async workflow for single panel generation."""

    # Initialize AI clients
    llm_client = OpenAIClient(api_key=settings.openai_api_key, model=settings.default_llm_model)

    image_generator = StabilityAIGenerator(api_key=settings.stability_ai_api_key)

    panel_processor = PanelProcessor(llm_client, image_generator)

    # Generate panel
    task.update_state(
        state=TaskStatus.RUNNING.value, meta={"progress": 50, "current_step": "Generating panel"}
    )

    panel_result = await panel_processor.generate_complete_panel(
        scene_description, characters, style, quality
    )

    task.update_state(
        state=TaskStatus.COMPLETED.value,
        meta={"progress": 100, "current_step": "Completed", "result": panel_result},
    )

    return panel_result
