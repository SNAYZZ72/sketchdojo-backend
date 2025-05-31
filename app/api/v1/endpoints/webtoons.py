# =============================================================================
# app/api/v1/endpoints/webtoons.py
# =============================================================================
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.domain.services.task_service import TaskService
from app.domain.services.webtoon_service import WebtoonService
from app.infrastructure.database.repositories.task_repository import TaskRepository
from app.infrastructure.database.repositories.webtoon_repository import WebtoonRepository
from app.schemas.task import TaskResponse
from app.schemas.user import UserResponse
from app.schemas.webtoon import (
    WebtoonCreate,
    WebtoonGenerateRequest,
    WebtoonResponse,
    WebtoonUpdate,
)
from app.tasks.webtoon_tasks import generate_complete_webtoon

router = APIRouter()


@router.post("", response_model=WebtoonResponse, status_code=status.HTTP_201_CREATED)
async def create_webtoon(
    webtoon_data: WebtoonCreate,
    project_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new webtoon."""
    webtoon_repo = WebtoonRepository(db)
    webtoon_service = WebtoonService(webtoon_repo)

    try:
        webtoon = await webtoon_service.create_webtoon(project_id, current_user.id, webtoon_data)
        return webtoon
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/generate", response_model=TaskResponse)
async def generate_webtoon(
    generation_request: WebtoonGenerateRequest,
    project_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start webtoon generation process."""
    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    # Check user limits
    if not current_user.can_generate_panel():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly generation limit exceeded",
        )

    # Create task record
    task_data = {
        "project_id": str(project_id),
        "story_prompt": generation_request.story_prompt,
        "style": generation_request.style_preferences.get("style", "webtoon"),
        "panel_count": generation_request.panel_count,
        "quality": generation_request.style_preferences.get("quality", "standard"),
    }

    task = await task_service.create_task(
        user_id=current_user.id, task_type="webtoon_generation", input_data=task_data
    )

    # Start background task
    celery_task = generate_complete_webtoon.delay(
        str(current_user.id),
        str(project_id),
        generation_request.story_prompt,
        generation_request.style_preferences.get("style", "webtoon"),
        generation_request.panel_count,
        generation_request.style_preferences.get("quality", "standard"),
    )

    # Update task with Celery ID
    await task_service.start_task(task.id, celery_task.id)

    return TaskResponse.model_validate(task)


@router.get("/{webtoon_id}", response_model=WebtoonResponse)
async def get_webtoon(
    webtoon_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific webtoon."""
    webtoon_repo = WebtoonRepository(db)
    webtoon_service = WebtoonService(webtoon_repo)

    try:
        webtoon = await webtoon_service.get_webtoon(webtoon_id, current_user.id)
        return webtoon
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this webtoon"
        )


@router.put("/{webtoon_id}", response_model=WebtoonResponse)
async def update_webtoon(
    webtoon_id: UUID,
    webtoon_data: WebtoonUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a webtoon."""
    webtoon_repo = WebtoonRepository(db)
    webtoon_service = WebtoonService(webtoon_repo)

    try:
        webtoon = await webtoon_service.update_webtoon(webtoon_id, current_user.id, webtoon_data)
        return webtoon
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this webtoon"
        )


@router.post("/{webtoon_id}/publish", response_model=WebtoonResponse)
async def publish_webtoon(
    webtoon_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a webtoon."""
    webtoon_repo = WebtoonRepository(db)
    webtoon_service = WebtoonService(webtoon_repo)

    try:
        webtoon = await webtoon_service.publish_webtoon(webtoon_id, current_user.id)
        return webtoon
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to publish this webtoon"
        )
