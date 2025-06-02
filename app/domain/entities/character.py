# app/domain/entities/character.py
"""
Character domain entity
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class CharacterAppearance:
    """Character appearance description"""

    height: str = ""
    build: str = ""
    hair_color: str = ""
    hair_style: str = ""
    eye_color: str = ""
    skin_tone: str = ""
    distinctive_features: List[str] = field(default_factory=list)
    clothing_style: str = ""

    def to_description(self) -> str:
        """Convert appearance to natural language description"""
        parts = []
        if self.height:
            parts.append(f"{self.height} height")
        if self.build:
            parts.append(f"{self.build} build")
        if self.hair_color and self.hair_style:
            parts.append(f"{self.hair_color} {self.hair_style} hair")
        if self.eye_color:
            parts.append(f"{self.eye_color} eyes")
        if self.skin_tone:
            parts.append(f"{self.skin_tone} skin")
        if self.clothing_style:
            parts.append(f"wearing {self.clothing_style}")
        if self.distinctive_features:
            parts.extend(self.distinctive_features)
        return ", ".join(parts)


@dataclass
class Character:
    """
    Character entity representing a webtoon character
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    appearance: CharacterAppearance = field(default_factory=CharacterAppearance)
    personality_traits: List[str] = field(default_factory=list)
    role: str = ""  # protagonist, antagonist, supporting, etc.
    relationships: Dict[str, str] = field(
        default_factory=dict
    )  # {character_name: relationship}
    backstory: str = ""
    goals: List[str] = field(default_factory=list)
    emotions: Dict[str, str] = field(
        default_factory=dict
    )  # {emotion: expression_description}

    def __post_init__(self):
        if not self.name:
            raise ValueError("Character name is required")

    def add_relationship(self, character_name: str, relationship: str) -> None:
        """Add a relationship with another character"""
        self.relationships[character_name] = relationship

    def get_full_description(self) -> str:
        """Get a comprehensive character description for AI prompts"""
        parts = [f"Character: {self.name}"]

        if self.description:
            parts.append(f"Description: {self.description}")

        appearance_desc = self.appearance.to_description()
        if appearance_desc:
            parts.append(f"Appearance: {appearance_desc}")

        if self.personality_traits:
            parts.append(f"Personality: {', '.join(self.personality_traits)}")

        if self.role:
            parts.append(f"Role: {self.role}")

        return ". ".join(parts)

    def get_emotion_expression(self, emotion: str) -> Optional[str]:
        """Get expression description for a specific emotion"""
        return self.emotions.get(emotion.lower())
