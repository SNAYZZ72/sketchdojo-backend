# =============================================================================
# app/domain/services/webtoon_service.py
# =============================================================================
import logging
from typing import List, Optional
from uuid import UUID

from app.domain.models.project import Project, ProjectStatus
from app.domain.models.webtoon import Webtoon, WebtoonStatus
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.webtoon import WebtoonCreate, WebtoonResponse, WebtoonUpdate

logger = logging.getLogger(__name__)


class WebtoonService:
    """Service for webtoon and project management."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        webtoon_repository: Optional[WebtoonRepository] = None,
    ):
        self.project_repo = project_repository
        self.webtoon_repo = webtoon_repository

    async def create_project(self, user_id: UUID, project_data: ProjectCreate) -> ProjectResponse:
        """Create a new project."""
        # Check user project limits
        user_projects = await self.project_repo.get_user_projects(user_id)
        # Would check against user.max_projects here

        # Create project domain object
        project = Project(
            user_id=user_id,
            title=project_data.title,
            description=project_data.description,
            story_outline=project_data.story_outline,
            target_panels=project_data.target_panels,
            art_style=project_data.art_style,
            color_palette=project_data.color_palette or [],
        )

        # Save to repository
        saved_project = await self.project_repo.create(project)

        logger.info(f"Project created: {saved_project.id} by user {user_id}")
        return ProjectResponse.model_validate(saved_project)

    async def get_project(self, project_id: UUID, user_id: UUID) -> ProjectResponse:
        """Get a project by ID."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        if project.user_id != user_id:
            raise PermissionError("Not authorized to access this project")

        return ProjectResponse.model_validate(project)

    async def update_project(
        self, project_id: UUID, user_id: UUID, project_data: ProjectUpdate
    ) -> ProjectResponse:
        """Update a project."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        if project.user_id != user_id:
            raise PermissionError("Not authorized to update this project")

        if not project.can_be_modified():
            raise ValueError("Project cannot be modified in its current status")

        # Update project fields
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        # Save changes
        updated_project = await self.project_repo.update(project)

        logger.info(f"Project updated: {project_id}")
        return ProjectResponse.model_validate(updated_project)

    async def delete_project(self, project_id: UUID, user_id: UUID):
        """Delete a project."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        if project.user_id != user_id:
            raise PermissionError("Not authorized to delete this project")

        await self.project_repo.delete(project_id)

        logger.info(f"Project deleted: {project_id}")

    async def create_webtoon(
        self, project_id: UUID, user_id: UUID, webtoon_data: WebtoonCreate
    ) -> WebtoonResponse:
        """Create a new webtoon."""
        if not self.webtoon_repo:
            raise ValueError("Webtoon repository not available")

        # Verify project ownership
        project = await self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to create webtoon for this project")

        # Create webtoon domain object
        webtoon = Webtoon(
            project_id=project_id,
            title=webtoon_data.title,
            description=webtoon_data.description,
            metadata=webtoon_data.metadata,
            story_summary=webtoon_data.story_summary,
            estimated_panels=webtoon_data.estimated_panels,
            art_style_reference=webtoon_data.art_style_reference,
            style_notes=webtoon_data.style_notes,
            color_palette=webtoon_data.color_palette or [],
        )

        # Save to repository
        saved_webtoon = await self.webtoon_repo.create(webtoon)

        # Update project status
        project.mark_in_progress()
        await self.project_repo.update(project)

        logger.info(f"Webtoon created: {saved_webtoon.id} for project {project_id}")
        return WebtoonResponse.model_validate(saved_webtoon)

    async def get_webtoon(self, webtoon_id: UUID, user_id: UUID) -> WebtoonResponse:
        """Get a webtoon by ID."""
        if not self.webtoon_repo:
            raise ValueError("Webtoon repository not available")

        webtoon = await self.webtoon_repo.get_by_id(webtoon_id)
        if not webtoon:
            raise ValueError("Webtoon not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(webtoon.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to access this webtoon")

        return WebtoonResponse.model_validate(webtoon)

    async def update_webtoon(
        self, webtoon_id: UUID, user_id: UUID, webtoon_data: WebtoonUpdate
    ) -> WebtoonResponse:
        """Update a webtoon."""
        if not self.webtoon_repo:
            raise ValueError("Webtoon repository not available")

        webtoon = await self.webtoon_repo.get_by_id(webtoon_id)
        if not webtoon:
            raise ValueError("Webtoon not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(webtoon.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to update this webtoon")

        # Update webtoon fields
        update_data = webtoon_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(webtoon, field):
                setattr(webtoon, field, value)

        # Save changes
        updated_webtoon = await self.webtoon_repo.update(webtoon)

        logger.info(f"Webtoon updated: {webtoon_id}")
        return WebtoonResponse.model_validate(updated_webtoon)

    async def publish_webtoon(self, webtoon_id: UUID, user_id: UUID) -> WebtoonResponse:
        """Publish a webtoon."""
        if not self.webtoon_repo:
            raise ValueError("Webtoon repository not available")

        webtoon = await self.webtoon_repo.get_by_id(webtoon_id)
        if not webtoon:
            raise ValueError("Webtoon not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(webtoon.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to publish this webtoon")

        if not webtoon.can_be_published():
            raise ValueError("Webtoon is not ready for publication")

        # Generate published URL (would be implemented based on storage strategy)
        published_url = f"https://sketchdojo.com/webtoons/{webtoon_id}"

        # Publish webtoon
        webtoon.publish(published_url)

        # Update project status
        project.mark_completed()
        await self.project_repo.update(project)

        # Save webtoon changes
        updated_webtoon = await self.webtoon_repo.update(webtoon)

        logger.info(f"Webtoon published: {webtoon_id}")
        return WebtoonResponse.model_validate(updated_webtoon)
