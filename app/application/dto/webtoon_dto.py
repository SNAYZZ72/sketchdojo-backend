# app/application/dto/webtoon_dto.py
"""
Webtoon Data Transfer Objects
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

# Using string literals for art style


class CharacterDTO(BaseModel):
    """Character data transfer object"""

    id: UUID
    name: str
    description: str
    appearance_description: str
    personality_traits: List[str]
    role: str


class PanelDTO(BaseModel):
    """Panel data transfer object"""

    id: UUID
    sequence_number: int
    scene_description: str
    character_names: List[str]
    dialogue: List[Dict[str, str]]
    visual_effects: List[str]
    image_url: Optional[str] = None
    generated_at: Optional[datetime] = None


class WebtoonDTO(BaseModel):
    """Webtoon data transfer object"""

    id: UUID
    title: str
    description: str
    art_style: str
    panels: List[PanelDTO]
    characters: List[CharacterDTO]
    created_at: datetime
    updated_at: datetime
    is_published: bool
    panel_count: int
    character_count: int
