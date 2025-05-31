# =============================================================================
# app/schemas/panel.py
# =============================================================================
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.models.panel import PanelLayout, PanelSize, PanelStatus

from .base import BaseEntitySchema


class SpeechBubbleSchema(BaseModel):
    """Schema for speech bubble."""

    character_id: UUID
    text: str = Field(min_length=1)
    position: Dict[str, float] = Field(description="Relative position {x: 0.0-1.0, y: 0.0-1.0}")
    style: str = Field(default="normal", pattern="^(normal|thought|shout|whisper|narration)$")
    tail_direction: str = Field(default="bottom", pattern="^(top|bottom|left|right)$")


class VisualElementSchema(BaseModel):
    """Schema for visual element."""

    element_type: str = Field(pattern="^(sound_effect|motion_lines|background_text)$")
    text: Optional[str] = None
    position: Dict[str, float] = Field(default_factory=dict)
    style_properties: Dict[str, Any] = Field(default_factory=dict)


class PanelBase(BaseModel):
    """Base panel schema."""

    visual_description: str = Field(min_length=1)
    size: PanelSize = PanelSize.MEDIUM
    layout: PanelLayout = PanelLayout.LANDSCAPE


class PanelCreate(PanelBase):
    """Schema for panel creation."""

    scene_id: Optional[UUID] = None
    sequence_number: int = Field(default=0, ge=0)
    characters_present: List[UUID] = Field(default_factory=list)
    speech_bubbles: List[SpeechBubbleSchema] = Field(default_factory=list)
    visual_elements: List[VisualElementSchema] = Field(default_factory=list)


class PanelUpdate(BaseModel):
    """Schema for panel updates."""

    visual_description: Optional[str] = Field(None, min_length=1)
    size: Optional[PanelSize] = None
    layout: Optional[PanelLayout] = None
    characters_present: Optional[List[UUID]] = None
    speech_bubbles: Optional[List[SpeechBubbleSchema]] = None
    visual_elements: Optional[List[VisualElementSchema]] = None
    feedback: Optional[str] = None
    revision_notes: Optional[str] = None


class PanelGenerateRequest(BaseModel):
    """Schema for panel generation request."""

    visual_description: str = Field(min_length=1)
    characters_present: List[UUID] = Field(default_factory=list)
    style_override: Optional[str] = None
    quality: str = Field(default="standard", pattern="^(draft|standard|high)$")


class PanelResponse(BaseEntitySchema):
    """Schema for panel response."""

    webtoon_id: UUID
    scene_id: Optional[UUID]
    sequence_number: int
    size: PanelSize
    layout: PanelLayout
    status: PanelStatus
    visual_description: str
    characters_present: List[UUID]
    speech_bubbles: List[SpeechBubbleSchema]
    visual_elements: List[VisualElementSchema]
    ai_prompt: Optional[str]
    image_url: Optional[str]
    generation_metadata: Optional[Dict[str, Any]]
    feedback: Optional[str]
    revision_notes: Optional[str]
