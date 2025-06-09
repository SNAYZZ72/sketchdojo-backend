# app/schemas/generation_schemas.py
"""
Generation-related API schemas
"""
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.domain.value_objects.style import ArtStyle


class GenerationRequest(BaseModel):
    """Request to generate a webtoon"""

    prompt: str = Field(..., min_length=10, max_length=2000, description="Story prompt")
    art_style: str = Field(default="webtoon", description="Art style")
    num_panels: int = Field(default=6, ge=1, le=20, description="Number of panels")
    character_descriptions: Optional[List[str]] = Field(
        default=None, description="Optional character descriptions"
    )
    additional_context: Optional[str] = Field(
        default=None, max_length=1000, description="Additional context"
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="Style preferences"
    )
    
    @validator('art_style')
    def validate_art_style(cls, v):
        if isinstance(v, ArtStyle):
            return v.value
        try:
            # Validate it's a valid art style
            return ArtStyle(v).value
        except ValueError:
            valid_styles = [s.value for s in ArtStyle]
            raise ValueError(f"Invalid art style. Must be one of: {', '.join(valid_styles)}")


class PanelGenerationRequest(BaseModel):
    """Request to generate a single panel"""

    scene_description: str = Field(..., min_length=10, max_length=1000)
    character_names: List[str] = Field(default_factory=list)
    art_style: str = Field(default="webtoon")
    panel_size: str = Field(default="full", pattern="^(full|half|third|quarter)$")
    mood: Optional[str] = Field(default=None, max_length=100)
    prompt: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=500,
        description="Optional prompt to guide image generation",
    )
    style_preferences: Optional[Dict[str, Any]] = Field(
        default=None, description="Style preferences for generation"
    )
    
    @validator('art_style')
    def validate_art_style(cls, v):
        if isinstance(v, ArtStyle):
            return v.value
        try:
            # Validate it's a valid art style
            return ArtStyle(v).value
        except ValueError:
            valid_styles = [s.value for s in ArtStyle]
            raise ValueError(f"Invalid art style. Must be one of: {', '.join(valid_styles)}")


class GenerationResponse(BaseModel):
    """Response for generation request"""

    task_id: UUID
    status: str
    message: str


class GenerationProgressResponse(BaseModel):
    """Generation progress update"""

    task_id: UUID
    progress_percentage: float = Field(ge=0, le=100)
    current_operation: str
    estimated_time_remaining: Optional[int] = None  # seconds


class GenerationResultResponse(BaseModel):
    """Generation result"""

    task_id: UUID
    webtoon_id: UUID
    title: str
    panel_count: int
    generation_time: float  # seconds
    result_url: str


class GenerationStatusResponse(BaseModel):
    """Generation status"""

    task_id: UUID
    status: str
    progress_percentage: float
    current_operation: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
