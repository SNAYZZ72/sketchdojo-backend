# app/api/v1/routes/generation.py
"""
Generation API routes
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

logger = logging.getLogger(__name__)

from app.application.services.generation_service import GenerationService
from app.dependencies import get_generation_service
from app.schemas.generation_schemas import (
    GenerationRequest,
    GenerationResponse,
    PanelGenerationRequest,
)

router = APIRouter()


@router.post("/webtoon", response_model=GenerationResponse)
async def generate_webtoon(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    service: GenerationService = Depends(get_generation_service),
):
    """Start webtoon generation process"""
    try:
        from app.application.dto.generation_dto import GenerationRequestDTO

        # Convert to DTO
        request_dto = GenerationRequestDTO(
            prompt=request.prompt,
            art_style=request.art_style,
            num_panels=request.num_panels,
            character_descriptions=request.character_descriptions,
            additional_context=request.additional_context,
            style_preferences=request.style_preferences,
        )

        # Start generation task
        result_dto = await service.start_webtoon_generation(request_dto)

        # Submit task to Celery for async processing using explicit task name
        from app.tasks.celery_app import celery_app
        logger.debug(f"Submitting task with task_id: {result_dto.task_id}")
        
        try:
            # Convert DTO to dict and ensure all data is JSON serializable
            request_dict = request_dto.dict()
            logger.debug(f"Request dict before serialization: {request_dict}")
            
            # Handle enums and other non-serializable objects
            if 'art_style' in request_dict:
                request_dict['art_style'] = request_dict['art_style'].value if hasattr(request_dict['art_style'], 'value') else str(request_dict['art_style'])
            
            # Ensure all values in style_preferences are serializable
            if 'style_preferences' in request_dict and request_dict['style_preferences']:
                for key, value in request_dict['style_preferences'].items():
                    if hasattr(value, 'value'):  # Handle potential enums in style preferences
                        request_dict['style_preferences'][key] = value.value
                    elif hasattr(value, '__dict__'):  # Handle custom objects
                        request_dict['style_preferences'][key] = str(value)
            
            # For safety, convert any remaining non-serializable objects to strings
            for key, value in request_dict.items():
                if hasattr(value, '__dict__') and not isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    request_dict[key] = str(value)
            
            logger.debug(f"Serialized request dict: {request_dict}")
            
            # Send the task to Celery
            celery_app.send_task(
                'app.tasks.generation_tasks.start_webtoon_generation_task',
                args=[str(result_dto.task_id), request_dict],
                queue='celery'  # Ensure the task is sent to the default queue
            )
        except Exception as e:
            logger.exception(f"Error sending task to Celery: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to schedule generation task: {str(e)}")

        return GenerationResponse(
            task_id=result_dto.task_id,
            status=result_dto.status,
            message="Generation started successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/panel", response_model=GenerationResponse)
async def generate_panel(
    request: PanelGenerationRequest,
    service: GenerationService = Depends(get_generation_service),
):
    """Generate a single panel"""
    try:
        # Start panel generation using the service
        result_dto = await service.start_panel_generation(
            scene_description=request.scene_description,
            art_style=request.art_style,
            character_names=request.character_names,
            panel_size=request.panel_size,
            mood=request.mood,
            prompt=request.prompt if hasattr(request, "prompt") else None,
            style_preferences=request.style_preferences
            if hasattr(request, "style_preferences")
            else None,
        )

        # Return the task information
        return GenerationResponse(
            task_id=result_dto.task_id,
            status=result_dto.status,
            message="Panel generation started successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-test", response_model=dict)
async def generate_webtoon_sync(
    prompt: str,
    art_style: str = "webtoon",
    num_panels: int = 4,
    service: GenerationService = Depends(get_generation_service),
):
    """Synchronous generation for testing (development only)"""
    try:
        from app.application.dto.generation_dto import GenerationRequestDTO
        from app.domain.value_objects.style import ArtStyle

        request_dto = GenerationRequestDTO(
            prompt=prompt, art_style=ArtStyle(art_style), num_panels=num_panels
        )

        result = await service.generate_webtoon_sync(request_dto)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
