# =============================================================================
# app/infrastructure/database/repositories/character_repository.py
# =============================================================================
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.character import Character, CharacterAppearance, CharacterPersonality
from app.domain.repositories.character_repository import (
    CharacterRepository as CharacterRepositoryInterface,
)
from app.infrastructure.database.models.character import CharacterModel

logger = logging.getLogger(__name__)


class CharacterRepository(CharacterRepositoryInterface):
    """SQLAlchemy implementation of CharacterRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: CharacterModel) -> Character:
        """Convert database model to domain entity."""
        return Character(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            role=model.role,
            description=model.description,
            appearance=CharacterAppearance(**model.appearance),
            personality=CharacterPersonality(**model.personality),
            reference_image_url=model.reference_image_url,
            style_notes=model.style_notes,
            relationships=model.relationships or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_db_model(self, entity: Character) -> CharacterModel:
        """Convert domain entity to database model."""
        return CharacterModel(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            role=entity.role,
            description=entity.description,
            appearance=entity.appearance.__dict__,
            personality=entity.personality.__dict__,
            reference_image_url=entity.reference_image_url,
            style_notes=entity.style_notes,
            relationships=entity.relationships,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def get(self, id: UUID) -> Optional[Character]:
        """Get character by ID."""
        query = select(CharacterModel).where(CharacterModel.id == id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def get_by_project_id(self, project_id: UUID) -> List[Character]:
        """Get all characters for a specific project."""
        query = select(CharacterModel).where(CharacterModel.project_id == project_id)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_by_name(self, project_id: UUID, name: str) -> Optional[Character]:
        """Get a character by name within a project."""
        query = select(CharacterModel).where(
            CharacterModel.project_id == project_id, CharacterModel.name == name
        )
        result = await self.session.execute(query)
        model = result.scalars().first()
        return self._to_domain(model) if model else None

    async def get_featured(self, limit: int = 10) -> List[Character]:
        """Get featured characters."""
        # This is a simplified implementation - in a real application you might
        # have more complex logic to determine featured characters
        query = select(CharacterModel).order_by(CharacterModel.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def create(self, entity: Character) -> Character:
        """Create a new character."""
        model = self._to_db_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def update(self, entity: Character) -> Character:
        """Update an existing character."""
        query = (
            update(CharacterModel)
            .where(CharacterModel.id == entity.id)
            .values(
                name=entity.name,
                role=entity.role,
                description=entity.description,
                appearance=entity.appearance.__dict__,
                personality=entity.personality.__dict__,
                reference_image_url=entity.reference_image_url,
                style_notes=entity.style_notes,
                relationships=entity.relationships,
                updated_at=entity.updated_at,
            )
            .returning(CharacterModel)
        )

        result = await self.session.execute(query)
        model = result.scalars().first()
        return self._to_domain(model)

    async def delete(self, id: UUID) -> None:
        """Delete a character."""
        query = select(CharacterModel).where(CharacterModel.id == id)
        result = await self.session.execute(query)
        model = result.scalars().first()
        if model:
            await self.session.delete(model)

    async def update_image(self, character_id: UUID, image_url: str) -> None:
        """Update character image URL."""
        query = (
            update(CharacterModel)
            .where(CharacterModel.id == character_id)
            .values(reference_image_url=image_url)
        )
        await self.session.execute(query)
