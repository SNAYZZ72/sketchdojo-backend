# =============================================================================
# app/schemas/project.py
# =============================================================================
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.project import ProjectStatus

from .base import BaseEntitySchema, PaginatedResponse


class ProjectBase(BaseModel):
    """Base project schema."""

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    art_style: str = Field(default="webtoon", pattern="^(webtoon|manga|comic)$")
    target_panels: int = Field(default=6, ge=1, le=20)


class ProjectCreate(ProjectBase):
    """Schema for project creation."""

    story_outline: Optional[str] = None
    color_palette: Optional[List[str]] = None


class ProjectUpdate(BaseModel):
    """Schema for project updates."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    story_outline: Optional[str] = None
    art_style: Optional[str] = Field(None, pattern="^(webtoon|manga|comic)$")
    target_panels: Optional[int] = Field(None, ge=1, le=20)
    color_palette: Optional[List[str]] = None


class ProjectResponse(BaseEntitySchema):
    """Schema for project response."""

    user_id: UUID
    title: str
    description: Optional[str]
    status: ProjectStatus
    thumbnail_url: Optional[str]
    story_outline: Optional[str]
    target_panels: int
    art_style: str
    color_palette: Optional[List[str]]
    project_metadata: Optional[Dict[str, Any]]


class ProjectListResponse(BaseModel):
    """Schema for project list response."""

    id: UUID
    title: str
    status: ProjectStatus
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime
