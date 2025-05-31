# =============================================================================
# app/domain/services/scene_service.py
# =============================================================================
import logging
from typing import List
from uuid import UUID

from app.domain.models.scene import Scene
from app.domain.repositories.base import BaseRepository
from app.schemas.scene import SceneCreate, SceneResponse, SceneUpdate

logger = logging.getLogger(__name__)


class SceneService:
    """Service for scene management."""

    def __init__(self, scene_repository: BaseRepository, project_repository: BaseRepository):
        self.scene_repo = scene_repository
        self.project_repo = project_repository

    async def create_scene(
        self, project_id: UUID, user_id: UUID, scene_data: SceneCreate
    ) -> SceneResponse:
        """Create a new scene."""
        # Verify project ownership
        project = await self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to create scenes for this project")

        # Create scene domain object
        scene = Scene(
            project_id=project_id,
            sequence_number=scene_data.sequence_number,
            scene_type=scene_data.scene_type,
            title=scene_data.title,
            description=scene_data.description,
            environment=scene_data.environment,
            characters_present=scene_data.characters_present or [],
            dialogue_lines=scene_data.dialogue_lines or [],
            action_description=scene_data.action_description,
            emotional_beats=scene_data.emotional_beats or [],
            camera_angle=scene_data.camera_angle,
            visual_focus=scene_data.visual_focus,
            special_effects=scene_data.special_effects or [],
        )

        # Save to repository
        saved_scene = await self.scene_repo.create(scene)

        logger.info(f"Scene created: {saved_scene.id} for project {project_id}")
        return SceneResponse.model_validate(saved_scene)

    async def get_scene(self, scene_id: UUID, user_id: UUID) -> SceneResponse:
        """Get a scene by ID."""
        scene = await self.scene_repo.get_by_id(scene_id)
        if not scene:
            raise ValueError("Scene not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(scene.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to access this scene")

        return SceneResponse.model_validate(scene)

    async def get_project_scenes(self, project_id: UUID, user_id: UUID) -> List[Scene]:
        """Get all scenes for a project."""
        # Verify project ownership
        project = await self.project_repo.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to access scenes for this project")

        scenes = await self.scene_repo.get_by_project_id(project_id)
        return scenes

    async def update_scene(
        self, scene_id: UUID, user_id: UUID, scene_data: SceneUpdate
    ) -> SceneResponse:
        """Update a scene."""
        scene = await self.scene_repo.get_by_id(scene_id)
        if not scene:
            raise ValueError("Scene not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(scene.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to update this scene")

        # Update scene fields
        update_data = scene_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(scene, field):
                setattr(scene, field, value)

        # Save changes
        updated_scene = await self.scene_repo.update(scene)

        logger.info(f"Scene updated: {scene_id}")
        return SceneResponse.model_validate(updated_scene)

    async def delete_scene(self, scene_id: UUID, user_id: UUID):
        """Delete a scene."""
        scene = await self.scene_repo.get_by_id(scene_id)
        if not scene:
            raise ValueError("Scene not found")

        # Check ownership through project
        project = await self.project_repo.get_by_id(scene.project_id)
        if not project or project.user_id != user_id:
            raise PermissionError("Not authorized to delete this scene")

        await self.scene_repo.delete(scene_id)

        logger.info(f"Scene deleted: {scene_id}")
