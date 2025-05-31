# =============================================================================
# app/api/v1/endpoints/scenes.py
# =============================================================================
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.domain.services.scene_service import SceneService
from app.infrastructure.database.repositories.project_repository import ProjectRepository
from app.infrastructure.database.repositories.scene_repository import SceneRepository
from app.schemas.scene import SceneCreate, SceneResponse, SceneUpdate
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/project/{project_id}", response_model=List[SceneResponse])
async def get_project_scenes(
    project_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all scenes for a project."""
    scene_repo = SceneRepository(db)
    project_repo = ProjectRepository(db)
    scene_service = SceneService(scene_repo, project_repo)

    try:
        scenes = await scene_service.get_project_scenes(project_id, current_user.id)
        return [SceneResponse.model_validate(scene) for scene in scenes]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access these scenes"
        )


@router.post("", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    scene_data: SceneCreate,
    project_id: UUID = Query(..., description="Project ID"),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new scene."""
    scene_repo = SceneRepository(db)
    project_repo = ProjectRepository(db)
    scene_service = SceneService(scene_repo, project_repo)

    try:
        scene = await scene_service.create_scene(project_id, current_user.id, scene_data)
        return scene
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create scenes for this project",
        )


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific scene."""
    scene_repo = SceneRepository(db)
    project_repo = ProjectRepository(db)
    scene_service = SceneService(scene_repo, project_repo)

    try:
        scene = await scene_service.get_scene(scene_id, current_user.id)
        return scene
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this scene"
        )


@router.put("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: UUID,
    scene_data: SceneUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a scene."""
    scene_repo = SceneRepository(db)
    project_repo = ProjectRepository(db)
    scene_service = SceneService(scene_repo, project_repo)

    try:
        scene = await scene_service.update_scene(scene_id, current_user.id, scene_data)
        return scene
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this scene"
        )


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene."""
    scene_repo = SceneRepository(db)
    project_repo = ProjectRepository(db)
    scene_service = SceneService(scene_repo, project_repo)

    try:
        await scene_service.delete_scene(scene_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this scene"
        )
