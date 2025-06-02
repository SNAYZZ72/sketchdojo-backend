# app/tasks/image_tasks.py
"""
Background tasks for image processing
"""
import logging
from typing import Any, Dict

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def generate_single_image_task(
    prompt: str, style: str, width: int = 1024, height: int = 1024
) -> Dict[str, Any]:
    """Background task for single image generation"""
    logger.info(f"Generating single image: {prompt[:50]}...")

    try:
        # Import here to avoid circular imports
        import asyncio

        from app.dependencies import get_image_generator

        image_generator = get_image_generator()

        if image_generator.is_available():
            local_path, public_url = asyncio.run(
                image_generator.generate_image(prompt, width, height, style)
            )

            return {"success": True, "local_path": local_path, "public_url": public_url}
        else:
            return {"success": False, "error": "Image generator not available"}

    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task
def process_image_batch(image_requests: list) -> Dict[str, Any]:
    """Process multiple images in batch"""
    logger.info(f"Processing image batch of {len(image_requests)} images")

    results = []
    for request in image_requests:
        result = generate_single_image_task.apply(
            args=[
                request.get("prompt"),
                request.get("style", "webtoon"),
                request.get("width", 1024),
                request.get("height", 1024),
            ]
        )
        results.append(result.get())

    return {
        "total_images": len(image_requests),
        "successful": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "results": results,
    }
