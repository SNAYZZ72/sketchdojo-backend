# =============================================================================
# app/api/v1/endpoints/panels.py
# =============================================================================
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.domain.services.panel_service import PanelService
from app.domain.services.task_service import TaskService
from app.infrastructure.database.repositories.panel_repository import PanelRepository
from app.infrastructure.database.repositories.task_repository import TaskRepository
from app.schemas.panel import PanelCreate, PanelGenerateRequest, PanelResponse, PanelUpdate
from app.schemas.task import TaskResponse
from app.schemas.user import UserResponse
from app.tasks.webtoon_tasks import generate_single_panel

router = APIRouter()


@router.get("/webtoon/{webtoon_id}", response_model=List[PanelResponse])
async def get_webtoon_panels(
    webtoon_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all panels for a webtoon."""
    panel_repo = PanelRepository(db)
    panel_service = PanelService(panel_repo)

    try:
        panels = await panel_service.get_webtoon_panels(webtoon_id, current_user.id)
        return [PanelResponse.model_validate(panel) for panel in panels]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access these panels"
        )


@router.post("", response_model=PanelResponse, status_code=status.HTTP_201_CREATED)
async def create_panel(
    panel_data: PanelCreate,
    webtoon_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new panel."""
    panel_repo = PanelRepository(db)
    panel_service = PanelService(panel_repo)

    try:
        panel = await panel_service.create_panel(webtoon_id, current_user.id, panel_data)
        return panel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/generate", response_model=TaskResponse)
async def generate_panel(
    generation_request: PanelGenerateRequest,
    webtoon_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start panel generation process."""
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
        "webtoon_id": str(webtoon_id),
        "visual_description": generation_request.visual_description,
        "characters_present": [str(c) for c in generation_request.characters_present],
        "style": generation_request.style_override or "webtoon",
        "quality": generation_request.quality,
    }

    task = await task_service.create_task(
        user_id=current_user.id, task_type="panel_generation", input_data=task_data
    )

    # For single panel generation, we need scene description and characters
    # This would normally come from the webtoon/project data
    scene_description = {
        "description": generation_request.visual_description,
        "characters_present": [str(c) for c in generation_request.characters_present],
    }

    # Start background task
    celery_task = generate_single_panel.delay(
        str(current_user.id),
        str(webtoon_id),
        scene_description,
        [],  # Characters data would be fetched from database
        generation_request.style_override or "webtoon",
        generation_request.quality,
    )

    # Update task with Celery ID
    await task_service.start_task(task.id, celery_task.id)

    return TaskResponse.model_validate(task)


@router.get("/{panel_id}", response_model=PanelResponse)
async def get_panel(
    panel_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific panel."""
    panel_repo = PanelRepository(db)
    panel_service = PanelService(panel_repo)

    try:
        panel = await panel_service.get_panel(panel_id, current_user.id)
        return panel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this panel"
        )


@router.put("/{panel_id}", response_model=PanelResponse)
async def update_panel(
    panel_id: UUID,
    panel_data: PanelUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a panel."""
    panel_repo = PanelRepository(db)
    panel_service = PanelService(panel_repo)

    try:
        panel = await panel_service.update_panel(panel_id, current_user.id, panel_data)
        return panel
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this panel"
        )


@router.delete("/{panel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_panel(
    panel_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a panel."""
    panel_repo = PanelRepository(db)
    panel_service = PanelService(panel_repo)

    try:
        await panel_service.delete_panel(panel_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this panel"
        )
