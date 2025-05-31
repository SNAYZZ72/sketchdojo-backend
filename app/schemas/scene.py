# =============================================================================
# app/schemas/scene.py
# =============================================================================
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.scene import SceneType, TimeOfDay

from .base import BaseEntitySchema


class SceneEnvironmentSchema(BaseModel):
    """Schema for scene environment."""

    location: str
    time_of_day: TimeOfDay
    weather: Optional[str] = None
    lighting: str = Field(default="natural", regex="^(natural|dramatic|soft|harsh)$")
    atmosphere: str = Field(default="neutral", regex="^(tense|peaceful|chaotic|romantic|neutral)$")


class DialogueLineSchema(BaseModel):
    """Schema for dialogue line."""

    character_id: UUID
    text: str = Field(min_length=1)
    emotion: str = Field(default="neutral")
    style: str = Field(default="normal", regex="^(whisper|shout|thought|narration|normal)$")


class SceneBase(BaseModel):
    """Base scene schema."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    scene_type: SceneType
    environment: SceneEnvironmentSchema


class SceneCreate(SceneBase):
    """Schema for scene creation."""

    sequence_number: int = Field(ge=1)
    characters_present: List[UUID] = Field(default_factory=list)
    dialogue_lines: List[DialogueLineSchema] = Field(default_factory=list)
    action_description: Optional[str] = None
    emotional_beats: List[str] = Field(default_factory=list)
    camera_angle: str = Field(default="medium", regex="^(close_up|medium|wide|extreme_wide)$")
    visual_focus: Optional[str] = None
    special_effects: List[str] = Field(default_factory=list)


class SceneUpdate(BaseModel):
    """Schema for scene updates."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    scene_type: Optional[SceneType] = None
    environment: Optional[SceneEnvironmentSchema] = None
    characters_present: Optional[List[UUID]] = None
    dialogue_lines: Optional[List[DialogueLineSchema]] = None
    action_description: Optional[str] = None
    emotional_beats: Optional[List[str]] = None
    camera_angle: Optional[str] = Field(None, regex="^(close_up|medium|wide|extreme_wide)$")
    visual_focus: Optional[str] = None
    special_effects: Optional[List[str]] = None


class SceneResponse(BaseEntitySchema):
    """Schema for scene response."""

    project_id: UUID
    sequence_number: int
    scene_type: SceneType
    title: str
    description: str
    environment: SceneEnvironmentSchema
    characters_present: List[UUID]
    dialogue_lines: List[DialogueLineSchema]
    action_description: Optional[str]
    emotional_beats: List[str]
    camera_angle: str
    visual_focus: Optional[str]
    special_effects: List[str]
