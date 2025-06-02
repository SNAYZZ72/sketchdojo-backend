# app/application/dto/generation_dto.py
"""
Generation Data Transfer Objects
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.value_objects.style import ArtStyle


class GenerationRequestDTO(BaseModel):
    """DTO for webtoon generation requests"""

    prompt: str = Field(..., description="Main story prompt")
    art_style: ArtStyle = Field(default=ArtStyle.WEBTOON, description="Art style")
    num_panels: int = Field(default=6, ge=1, le=20, description="Number of panels")
    character_descriptions: Optional[List[str]] = Field(
        default=None, description="Character descriptions"
    )
    additional_context: Optional[str] = Field(
        default=None, description="Additional context"
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="Style preferences"
    )


class PanelGenerationRequestDTO(BaseModel):
    """DTO for individual panel generation"""

    scene_description: str = Field(..., description="Scene description")
    character_names: List[str] = Field(
        default_factory=list, description="Characters in scene"
    )
    art_style: ArtStyle = Field(default=ArtStyle.WEBTOON, description="Art style")
    panel_size: str = Field(default="full", description="Panel size")
    mood: Optional[str] = Field(default=None, description="Scene mood")


class GenerationResultDTO(BaseModel):
    """DTO for generation results"""

    task_id: UUID
    webtoon_id: Optional[UUID] = None
    status: str
    progress_percentage: float
    current_operation: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
