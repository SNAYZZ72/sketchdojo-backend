"""
Final API Endpoints & Integration Tests
Files: app/api/v1/endpoints/characters.py, app/api/v1/endpoints/scenes.py, tests/
"""

from typing import List
from uuid import UUID

# =============================================================================
# app/api/v1/endpoints/characters.py
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.domain.services.character_service import CharacterService
from app.infrastructure.database.repositories.character_repository import CharacterRepository
from app.infrastructure.database.repositories.project_repository import ProjectRepository
from app.schemas.character import CharacterCreate, CharacterResponse, CharacterUpdate
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/project/{project_id}", response_model=List[CharacterResponse])
async def get_project_characters(
    project_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all characters for a project."""
    character_repo = CharacterRepository(db)
    project_repo = ProjectRepository(db)
    character_service = CharacterService(character_repo, project_repo)

    try:
        characters = await character_service.get_project_characters(project_id, current_user.id)
        return [CharacterResponse.from_orm(char) for char in characters]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these characters",
        )


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    project_id: UUID = Query(..., description="Project ID"),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new character."""
    character_repo = CharacterRepository(db)
    project_repo = ProjectRepository(db)
    character_service = CharacterService(character_repo, project_repo)

    try:
        character = await character_service.create_character(
            project_id, current_user.id, character_data
        )
        return character
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create characters for this project",
        )


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific character."""
    character_repo = CharacterRepository(db)
    project_repo = ProjectRepository(db)
    character_service = CharacterService(character_repo, project_repo)

    try:
        character = await character_service.get_character(character_id, current_user.id)
        return character
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this character"
        )


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: UUID,
    character_data: CharacterUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a character."""
    character_repo = CharacterRepository(db)
    project_repo = ProjectRepository(db)
    character_service = CharacterService(character_repo, project_repo)

    try:
        character = await character_service.update_character(
            character_id, current_user.id, character_data
        )
        return character
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this character"
        )


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a character."""
    character_repo = CharacterRepository(db)
    project_repo = ProjectRepository(db)
    character_service = CharacterService(character_repo, project_repo)

    try:
        await character_service.delete_character(character_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this character"
        )
