# app/domain/entities/webtoon.py
"""
Webtoon domain entity
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Optional
from uuid import UUID, uuid4

from app.domain.entities.character import Character
from app.domain.entities.panel import Panel
from app.domain.value_objects.style import ArtStyle


@dataclass
class Webtoon:
    """
    Core webtoon entity representing a complete webtoon project
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    art_style: ArtStyle = field(default_factory=lambda: ArtStyle.WEBTOON)
    panels: List[Panel] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_published: bool = False
    metadata: dict = field(default_factory=dict)

    def add_panel(self, panel: Panel) -> None:
        """Add a panel to the webtoon"""
        panel.sequence_number = len(self.panels)
        self.panels.append(panel)
        self.updated_at = datetime.now(UTC)

    def remove_panel(self, panel_id: UUID) -> bool:
        """Remove a panel by ID"""
        for i, panel in enumerate(self.panels):
            if panel.id == panel_id:
                del self.panels[i]
                # Resequence remaining panels
                for j, remaining_panel in enumerate(self.panels[i:], start=i):
                    remaining_panel.sequence_number = j
                self.updated_at = datetime.now(UTC)
                return True
        return False

    def add_character(self, character: Character) -> None:
        """Add a character to the webtoon"""
        self.characters.append(character)
        self.updated_at = datetime.now(UTC)

    def get_panel_by_id(self, panel_id: UUID) -> Optional[Panel]:
        """Get a panel by its ID"""
        return next((panel for panel in self.panels if panel.id == panel_id), None)

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get a character by name"""
        return next((char for char in self.characters if char.name == name), None)

    @property
    def panel_count(self) -> int:
        """Get the total number of panels"""
        return len(self.panels)

    @property
    def character_count(self) -> int:
        """Get the total number of characters"""
        return len(self.characters)
