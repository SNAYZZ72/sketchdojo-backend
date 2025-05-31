# =============================================================================
# app/domain/services/character_service.py
# =============================================================================
import logging
from typing import List
from uuid import UUID

from app.domain.models.character import Character
from app.domain.repositories.base import BaseRepository
from app.schemas.character import CharacterCreate, CharacterResponse, CharacterUpdate

logger = logging.getLogger(__name__)


class CharacterService:
    """Service for character management."""

    def __init__(self, character_repository: BaseRepository, project_repository: BaseRepository):
        self.character_repo = character_repository
        self.project_repo = project_repository

    async def create_character(
        self, project_id: UUID, user_id: UUID, character_data: CharacterCreate
    ) -> CharacterResponse:
        """Create a new character."""
        # Verify project ownership
        project = await self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to create characters for this project")

        # Create character domain object
        character = Character(
            project_id=project_id,
            name=character_data.name,
            role=character_data.role,
            description=character_data.description,
            appearance=character_data.appearance,
            personality=character_data.personality,
            reference_image_url=character_data.reference_image_url,
            style_notes=character_data.style_notes,
        )

        # Save to repository
        saved_character = await self.character_repo.create(character)

        logger.info(f"Character created: {saved_character.id} for project {project_id}")
        return CharacterResponse.from_orm(saved_character)

    async def get_character(self, character_id: UUID, user_id: UUID) -> CharacterResponse:
        """Get a character by ID."""
        character = await self.character_repo.get_by_id(character_id)
        if not character:
            raise ValueError("Character not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(character.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to access this character")

        return CharacterResponse.from_orm(character)

    async def get_project_characters(self, project_id: UUID, user_id: UUID) -> List[Character]:
        """Get all characters for a project."""
        # Verify project ownership
        project = await self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to access characters for this project")

        characters = await self.character_repo.get_by_project_id(project_id)
        return characters

    async def update_character(
        self, character_id: UUID, user_id: UUID, character_data: CharacterUpdate
    ) -> CharacterResponse:
        """Update a character."""
        character = await self.character_repo.get_by_id(character_id)
        if not character:
            raise ValueError("Character not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(character.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to update this character")

        # Update character fields
        update_data = character_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(character, field):
                setattr(character, field, value)

        # Save changes
        updated_character = await self.character_repo.update(character)

        logger.info(f"Character updated: {character_id}")
        return CharacterResponse.from_orm(updated_character)

    async def delete_character(self, character_id: UUID, user_id: UUID):
        """Delete a character."""
        character = await self.character_repo.get_by_id(character_id)
        if not character:
            raise ValueError("Character not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(character.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to delete this character")

        await self.character_repo.delete(character_id)

        logger.info(f"Character deleted: {character_id}")
