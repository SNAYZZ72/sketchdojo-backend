# =============================================================================
# app/domain/models/panel.py
# =============================================================================
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import DomainEntity


class PanelSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    FULL_WIDTH = "full_width"


class PanelLayout(str, Enum):
    SQUARE = "square"
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"
    CINEMATIC = "cinematic"


class PanelStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    GENERATED = "generated"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"


@dataclass
class SpeechBubble:
    """Speech bubble in a panel."""

    character_id: UUID
    text: str
    position: Dict[str, float]  # {"x": 0.5, "y": 0.3} - relative positions
    style: str = "normal"  # "thought", "shout", "whisper", "narration"
    tail_direction: str = "bottom"  # "top", "bottom", "left", "right"


@dataclass
class VisualElement:
    """Visual element in a panel (sound effects, etc.)."""

    element_type: str  # "sound_effect", "motion_lines", "background_text"
    text: Optional[str] = None
    position: Dict[str, float] = field(default_factory=dict)
    style_properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Panel(DomainEntity):
    """Panel domain model."""

    webtoon_id: UUID
    scene_id: Optional[UUID] = None
    sequence_number: int = 0

    # Visual properties
    size: PanelSize = PanelSize.MEDIUM
    layout: PanelLayout = PanelLayout.LANDSCAPE
    status: PanelStatus = PanelStatus.DRAFT

    # Content
    visual_description: str = ""
    characters_present: List[UUID] = field(default_factory=list)
    speech_bubbles: List[SpeechBubble] = field(default_factory=list)
    visual_elements: List[VisualElement] = field(default_factory=list)

    # Generation data
    ai_prompt: Optional[str] = None
    image_url: Optional[str] = None
    generation_metadata: Dict[str, Any] = field(default_factory=dict)

    # Review and feedback
    feedback: Optional[str] = None
    revision_notes: Optional[str] = None

    def add_speech_bubble(self, character_id: UUID, text: str, position: Dict[str, float]) -> None:
        """Add a speech bubble to the panel."""
        bubble = SpeechBubble(character_id=character_id, text=text, position=position)
        self.speech_bubbles.append(bubble)

    def add_visual_element(self, element_type: str, text: Optional[str] = None) -> None:
        """Add a visual element to the panel."""
        element = VisualElement(element_type=element_type, text=text)
        self.visual_elements.append(element)

    def mark_generating(self) -> None:
        """Mark panel as currently generating."""
        self.status = PanelStatus.GENERATING

    def mark_generated(self, image_url: str) -> None:
        """Mark panel as successfully generated."""
        self.status = PanelStatus.GENERATED
        self.image_url = image_url

    def mark_approved(self) -> None:
        """Mark panel as approved."""
        if self.status == PanelStatus.GENERATED:
            self.status = PanelStatus.APPROVED
