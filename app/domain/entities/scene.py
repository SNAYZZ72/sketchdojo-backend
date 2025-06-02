# app/domain/entities/scene.py
"""
Scene domain entity
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID, uuid4


@dataclass
class Scene:
    """
    Scene entity representing the visual content of a panel
    """

    id: UUID = field(default_factory=uuid4)
    description: str = ""
    setting: str = ""
    time_of_day: str = ""
    weather: str = ""
    mood: str = ""
    character_names: List[str] = field(default_factory=list)
    character_positions: Dict[str, str] = field(
        default_factory=dict
    )  # {character: position}
    character_expressions: Dict[str, str] = field(
        default_factory=dict
    )  # {character: expression}
    actions: List[str] = field(default_factory=list)
    camera_angle: str = "medium"  # close-up, medium, wide, bird's-eye, etc.
    lighting: str = "natural"  # natural, dramatic, soft, harsh, etc.
    composition_notes: str = ""

    def add_character(
        self, name: str, position: str = "", expression: str = ""
    ) -> None:
        """Add a character to the scene"""
        if name not in self.character_names:
            self.character_names.append(name)
        if position:
            self.character_positions[name] = position
        if expression:
            self.character_expressions[name] = expression

    def set_character_expression(self, character_name: str, expression: str) -> None:
        """Set expression for a character in the scene"""
        if character_name in self.character_names:
            self.character_expressions[character_name] = expression

    def get_prompt_description(self) -> str:
        """Generate a description suitable for AI image generation"""
        parts = []

        # Basic scene description
        if self.description:
            parts.append(self.description)

        # Setting and environment
        environment_parts = []
        if self.setting:
            environment_parts.append(f"Setting: {self.setting}")
        if self.time_of_day:
            environment_parts.append(f"Time: {self.time_of_day}")
        if self.weather:
            environment_parts.append(f"Weather: {self.weather}")
        if environment_parts:
            parts.append(", ".join(environment_parts))

        # Characters and their states
        if self.character_names:
            char_descriptions = []
            for char_name in self.character_names:
                char_desc = [char_name]
                if char_name in self.character_positions:
                    char_desc.append(
                        f"positioned {self.character_positions[char_name]}"
                    )
                if char_name in self.character_expressions:
                    char_desc.append(
                        f"with {self.character_expressions[char_name]} expression"
                    )
                char_descriptions.append(" ".join(char_desc))
            parts.append(f"Characters: {', '.join(char_descriptions)}")

        # Actions
        if self.actions:
            parts.append(f"Actions: {', '.join(self.actions)}")

        # Technical aspects
        tech_parts = []
        if self.camera_angle != "medium":
            tech_parts.append(f"{self.camera_angle} shot")
        if self.lighting != "natural":
            tech_parts.append(f"{self.lighting} lighting")
        if tech_parts:
            parts.append(", ".join(tech_parts))

        # Mood
        if self.mood:
            parts.append(f"Mood: {self.mood}")

        # Composition notes
        if self.composition_notes:
            parts.append(self.composition_notes)

        return ". ".join(parts)

    @property
    def character_count(self) -> int:
        """Get the number of characters in the scene"""
        return len(self.character_names)
