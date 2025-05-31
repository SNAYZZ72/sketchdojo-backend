# =============================================================================
# app/domain/models/character.py
# =============================================================================
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from .base import DomainEntity


@dataclass
class CharacterAppearance:
    """Character appearance details."""

    age_range: str  # "child", "teen", "young_adult", "adult", "elderly"
    gender: str
    height: str  # "short", "average", "tall"
    build: str  # "slim", "average", "muscular", "heavy"
    hair_color: str
    hair_style: str
    eye_color: str
    skin_tone: str
    distinctive_features: List[str] = field(default_factory=list)


@dataclass
class CharacterPersonality:
    """Character personality traits."""

    traits: List[str] = field(default_factory=list)
    motivations: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    speech_style: str = "normal"  # "formal", "casual", "rough", "elegant"


@dataclass
class Character(DomainEntity):
    """Character domain model."""

    project_id: UUID
    name: str
    role: str  # "protagonist", "antagonist", "supporting", "background"
    description: str
    appearance: CharacterAppearance
    personality: CharacterPersonality

    # Visual consistency
    reference_image_url: Optional[str] = None
    style_notes: Optional[str] = None
    relationships: Dict[UUID, str] = field(default_factory=dict)  # character_id -> relationship

    def add_relationship(self, character_id: UUID, relationship: str) -> None:
        """Add a relationship with another character."""
        self.relationships[character_id] = relationship

    def get_relationship(self, character_id: UUID) -> Optional[str]:
        """Get relationship with another character."""
        return self.relationships.get(character_id)
