# app/domain/entities/panel.py
"""
Panel domain entity
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.domain.entities.scene import Scene
from app.domain.value_objects.dimensions import PanelDimensions
from app.domain.value_objects.position import Position


@dataclass
class SpeechBubble:
    """Speech bubble within a panel"""

    id: UUID = field(default_factory=uuid4)
    character_name: str = ""
    text: str = ""
    position: Position = field(default_factory=Position)
    style: str = "normal"  # normal, thought, shout, whisper
    tail_direction: str = "bottom"  # top, right, bottom, left

    def __post_init__(self):
        if not self.character_name:
            raise ValueError("Character name is required for speech bubble")
        if not self.text:
            raise ValueError("Text is required for speech bubble")


@dataclass
class Panel:
    """
    Panel entity representing a single webtoon panel
    """

    id: UUID = field(default_factory=uuid4)
    sequence_number: int = 0
    scene: Scene = field(default_factory=Scene)
    dimensions: PanelDimensions = field(default_factory=PanelDimensions)
    speech_bubbles: List[SpeechBubble] = field(default_factory=list)
    visual_effects: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    generated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_speech_bubble(self, bubble: SpeechBubble) -> None:
        """Add a speech bubble to the panel"""
        self.speech_bubbles.append(bubble)

    def remove_speech_bubble(self, bubble_id: UUID) -> bool:
        """Remove a speech bubble by ID"""
        for i, bubble in enumerate(self.speech_bubbles):
            if bubble.id == bubble_id:
                del self.speech_bubbles[i]
                return True
        return False

    def add_visual_effect(self, effect: str) -> None:
        """Add a visual effect to the panel"""
        if effect not in self.visual_effects:
            self.visual_effects.append(effect)

    def get_dialogue_text(self) -> List[str]:
        """Get all dialogue text from speech bubbles"""
        return [bubble.text for bubble in self.speech_bubbles]

    def get_characters_in_panel(self) -> List[str]:
        """Get unique character names in this panel"""
        characters = set(self.scene.character_names)
        characters.update(bubble.character_name for bubble in self.speech_bubbles)
        return list(characters)

    @property
    def has_dialogue(self) -> bool:
        """Check if panel has any dialogue"""
        return len(self.speech_bubbles) > 0
