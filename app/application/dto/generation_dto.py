# app/application/dto/generation_dto.py
"""
Generation Data Transfer Objects
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Import from centralized constants
from app.domain.constants.art_styles import ensure_art_style_string, VALID_ART_STYLES


class GenerationRequestDTO(BaseModel):
    """DTO for webtoon generation requests"""

    prompt: str = Field(..., description="Main story prompt")
    art_style: str = Field(default="webtoon", description="Art style")
    num_panels: int = Field(default=6, ge=1, le=20, description="Number of panels")
    
    @field_validator('art_style')
    def validate_art_style(cls, v):
        """Validate that the art style is one of the valid options"""
        if v.lower() not in [s.lower() for s in VALID_ART_STYLES]:
            raise ValueError(f"Invalid art style: {v}. Must be one of {VALID_ART_STYLES}")
        return v.lower()
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
    art_style: str = Field(default="webtoon", description="Art style")
    panel_size: str = Field(default="full", description="Panel size")
    mood: Optional[str] = Field(default=None, description="Scene mood")
    
    @field_validator('art_style')
    def validate_art_style(cls, v):
        """Validate that the art style is one of the valid options"""
        if v.lower() not in [s.lower() for s in VALID_ART_STYLES]:
            raise ValueError(f"Invalid art style: {v}. Must be one of {VALID_ART_STYLES}")
        return v.lower()


class GenerationResultDTO(BaseModel):
    """DTO for generation results"""

    task_id: UUID
    webtoon_id: Optional[UUID] = None
    status: str
    progress_percentage: float
    current_operation: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
