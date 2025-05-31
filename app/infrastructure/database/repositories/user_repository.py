# =============================================================================
# app/infrastructure/database/repositories/user_repository.py
# =============================================================================
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User, UserRole, UserStatus
from app.domain.repositories.user_repository import UserRepository as UserRepositoryInterface
from app.infrastructure.database.models.user import UserModel

logger = logging.getLogger(__name__)


class UserRepository(UserRepositoryInterface):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            hashed_password=model.hashed_password,
            role=model.role,
            status=model.status,
            is_verified=model.is_verified,
            profile_image_url=model.profile_image_url,
            max_projects=model.max_projects,
            max_panels_per_webtoon=model.max_panels_per_webtoon,
            monthly_generation_limit=model.monthly_generation_limit,
            current_month_generations=model.current_month_generations,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Convert domain entity to database model."""
        return UserModel(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            hashed_password=entity.hashed_password,
            role=entity.role,
            status=entity.status,
            is_verified=entity.is_verified,
            profile_image_url=entity.profile_image_url,
            max_projects=entity.max_projects,
            max_panels_per_webtoon=entity.max_panels_per_webtoon,
            monthly_generation_limit=entity.monthly_generation_limit,
            current_month_generations=entity.current_month_generations,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, entity: User) -> User:
        """Create a new user."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        logger.info(f"User created: {model.id}")
        return self._to_domain(model)

    async def get_by_id(self, entity_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == entity_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(select(UserModel).where(UserModel.username == username))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def update(self, entity: User) -> User:
        """Update an existing user."""
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == entity.id)
            .values(
                email=entity.email,
                username=entity.username,
                hashed_password=entity.hashed_password,
                role=entity.role,
                status=entity.status,
                is_verified=entity.is_verified,
                profile_image_url=entity.profile_image_url,
                max_projects=entity.max_projects,
                max_panels_per_webtoon=entity.max_panels_per_webtoon,
                monthly_generation_limit=entity.monthly_generation_limit,
                current_month_generations=entity.current_month_generations,
                updated_at=entity.updated_at,
            )
        )

        # Fetch updated model
        result = await self.session.execute(select(UserModel).where(UserModel.id == entity.id))
        model = result.scalar_one()

        logger.info(f"User updated: {entity.id}")
        return self._to_domain(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a user by ID."""
        result = await self.session.execute(select(UserModel).where(UserModel.id == entity_id))
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            logger.info(f"User deleted: {entity_id}")
            return True

        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination."""
        result = await self.session.execute(
            select(UserModel).limit(limit).offset(offset).order_by(UserModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        from datetime import datetime

        await self.session.execute(
            update(UserModel).where(UserModel.id == user_id).values(updated_at=datetime.utcnow())
        )
