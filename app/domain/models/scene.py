# =============================================================================
# app/domain/models/scene.py
# =============================================================================
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import DomainEntity


class SceneType(str, Enum):
    DIALOGUE = "dialogue"
    ACTION = "action"
    EMOTIONAL = "emotional"
    TRANSITION = "transition"
    ESTABLISHING = "establishing"


class TimeOfDay(str, Enum):
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    NIGHT = "night"


@dataclass
class SceneEnvironment:
    """Scene environment and setting."""

    location: str
    time_of_day: TimeOfDay
    weather: Optional[str] = None
    lighting: str = "natural"  # "natural", "dramatic", "soft", "harsh"
    atmosphere: str = "neutral"  # "tense", "peaceful", "chaotic", "romantic"


@dataclass
class DialogueLine:
    """A line of dialogue in a scene."""

    character_id: UUID
    text: str
    emotion: str = "neutral"
    style: str = "normal"  # "whisper", "shout", "thought", "narration"


@dataclass
class Scene(DomainEntity):
    """Scene domain model."""

    project_id: UUID
    sequence_number: int
    scene_type: SceneType
    title: str
    description: str
    environment: SceneEnvironment

    # Content
    characters_present: List[UUID] = field(default_factory=list)
    dialogue_lines: List[DialogueLine] = field(default_factory=list)
    action_description: Optional[str] = None
    emotional_beats: List[str] = field(default_factory=list)

    # Visual direction
    camera_angle: str = "medium"  # "close_up", "medium", "wide", "extreme_wide"
    visual_focus: Optional[str] = None
    special_effects: List[str] = field(default_factory=list)

    def add_dialogue(self, character_id: UUID, text: str, emotion: str = "neutral") -> None:
        """Add a dialogue line to the scene."""
        dialogue = DialogueLine(character_id=character_id, text=text, emotion=emotion)
        self.dialogue_lines.append(dialogue)

    def add_character(self, character_id: UUID) -> None:
        """Add a character to the scene."""
        if character_id not in self.characters_present:
            self.characters_present.append(character_id)
