# =============================================================================
# app/schemas/webtoon.py
# =============================================================================
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.webtoon import WebtoonGenre, WebtoonStatus

from .base import BaseEntitySchema


class WebtoonMetadataSchema(BaseModel):
    """Schema for webtoon metadata."""

    genre: WebtoonGenre
    target_audience: str = Field(pattern="^(children|teen|young_adult|adult)$")
    content_rating: str = Field(pattern="^(G|PG|PG-13|R)$")
    tags: List[str] = Field(default_factory=list)
    color_scheme: str = Field(
        default="full_color", pattern="^(full_color|limited_color|monochrome)$"
    )
    aspect_ratio: str = Field(default="vertical", pattern="^(vertical|square|horizontal)$")


class WebtoonBase(BaseModel):
    """Base webtoon schema."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)


class WebtoonCreate(WebtoonBase):
    """Schema for webtoon creation."""

    webtoon_metadata: WebtoonMetadataSchema
    story_summary: Optional[str] = None
    estimated_panels: int = Field(default=6, ge=1, le=50)
    art_style_reference: Optional[str] = None
    style_notes: Optional[str] = None
    color_palette: List[str] = Field(default_factory=list)


class WebtoonUpdate(BaseModel):
    """Schema for webtoon updates."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    webtoon_metadata: Optional[WebtoonMetadataSchema] = None
    story_summary: Optional[str] = None
    estimated_panels: Optional[int] = Field(None, ge=1, le=50)
    art_style_reference: Optional[str] = None
    style_notes: Optional[str] = None
    color_palette: Optional[List[str]] = None


class WebtoonGenerateRequest(BaseModel):
    """Schema for webtoon generation request."""

    story_prompt: str = Field(min_length=10)
    character_descriptions: List[str] = Field(default_factory=list)
    style_preferences: Dict[str, Any] = Field(default_factory=dict)
    auto_generate_panels: bool = True
    panel_count: int = Field(default=6, ge=1, le=20)


class WebtoonResponse(BaseEntitySchema):
    """Schema for webtoon response."""

    project_id: UUID
    title: str
    description: str
    status: WebtoonStatus
    webtoon_metadata: WebtoonMetadataSchema
    story_summary: Optional[str]
    panel_count: int
    estimated_panels: int
    art_style_reference: Optional[str]
    style_notes: Optional[str]
    color_palette: Optional[List[str]]
    thumbnail_url: Optional[str]
    published_url: Optional[str]
    view_count: int
    like_count: int
