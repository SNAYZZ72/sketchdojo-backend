# app/schemas/webtoon_schemas.py
"""
Webtoon-related API schemas
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.webtoon_dto import CharacterDTO, PanelDTO, WebtoonDTO
# Using string literals for art style
from app.schemas.common_schemas import TimestampMixin


class CharacterAppearanceRequest(BaseModel):
    """Character appearance in requests"""

    height: str = ""
    build: str = ""
    hair_color: str = ""
    hair_style: str = ""
    eye_color: str = ""
    skin_tone: str = ""
    distinctive_features: List[str] = Field(default_factory=list)
    clothing_style: str = ""


class CharacterCreateRequest(BaseModel):
    """Request to create a character"""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    appearance: CharacterAppearanceRequest = Field(
        default_factory=CharacterAppearanceRequest
    )
    personality_traits: List[str] = Field(default_factory=list)
    role: str = Field(default="character", max_length=50)


class CharacterResponse(BaseModel):
    """Character response schema"""

    id: UUID
    name: str
    description: str
    appearance_description: str
    personality_traits: List[str]
    role: str

    @classmethod
    def from_dto(cls, dto: CharacterDTO) -> "CharacterResponse":
        return cls(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            appearance_description=dto.appearance_description,
            personality_traits=dto.personality_traits,
            role=dto.role,
        )


class PanelCreateRequest(BaseModel):
    """Request to create a panel"""

    scene_description: str = Field(..., min_length=10, max_length=1000)
    character_names: List[str] = Field(default_factory=list)
    panel_size: str = Field(default="full", pattern="^(full|half|third|quarter)$")
    visual_effects: List[str] = Field(default_factory=list)


class DialogueResponse(BaseModel):
    """Dialogue response schema"""

    character: str
    text: str


class PanelResponse(BaseModel):
    """Panel response schema"""

    id: UUID
    sequence_number: int
    scene_description: str
    character_names: List[str]
    dialogue: List[DialogueResponse]
    visual_effects: List[str]
    image_url: Optional[str] = None
    generated_at: Optional[datetime] = None

    @classmethod
    def from_dto(cls, dto: PanelDTO) -> "PanelResponse":
        dialogue = [
            DialogueResponse(character=d["character"], text=d["text"])
            for d in dto.dialogue
        ]

        return cls(
            id=dto.id,
            sequence_number=dto.sequence_number,
            scene_description=dto.scene_description,
            character_names=dto.character_names,
            dialogue=dialogue,
            visual_effects=dto.visual_effects,
            image_url=dto.image_url,
            generated_at=dto.generated_at,
        )


class WebtoonCreateRequest(BaseModel):
    """Request to create a webtoon"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    art_style: str = Field(default="webtoon", pattern="^(manga|webtoon|comic|anime|realistic|sketch|chibi)$")


class WebtoonResponse(TimestampMixin):
    """Webtoon response schema"""

    id: UUID
    title: str
    description: str
    art_style: str
    panels: List[PanelResponse]
    characters: List[CharacterResponse]
    is_published: bool
    panel_count: int
    character_count: int

    @classmethod
    def from_dto(cls, dto: WebtoonDTO) -> "WebtoonResponse":
        return cls(
            id=dto.id,
            title=dto.title,
            description=dto.description,
            art_style=dto.art_style,
            panels=[PanelResponse.from_dto(p) for p in dto.panels],
            characters=[CharacterResponse.from_dto(c) for c in dto.characters],
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            is_published=dto.is_published,
            panel_count=dto.panel_count,
            character_count=dto.character_count,
        )


class WebtoonListResponse(BaseModel):
    """Response for webtoon listing"""

    webtoons: List[WebtoonResponse]
    total: int
