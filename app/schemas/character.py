# =============================================================================
# app/schemas/character.py
# =============================================================================
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseEntitySchema


class CharacterAppearanceSchema(BaseModel):
    """Schema for character appearance."""

    age_range: str = Field(pattern="^(child|teen|young_adult|adult|elderly)$")
    gender: str
    height: str = Field(pattern="^(short|average|tall)$")
    build: str = Field(pattern="^(slim|average|muscular|heavy)$")
    hair_color: str
    hair_style: str
    eye_color: str
    skin_tone: str
    distinctive_features: List[str] = Field(default_factory=list)


class CharacterPersonalitySchema(BaseModel):
    """Schema for character personality."""

    traits: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)
    fears: List[str] = Field(default_factory=list)
    speech_style: str = Field(default="normal", pattern="^(formal|casual|rough|elegant|normal)$")


class CharacterBase(BaseModel):
    """Base character schema."""

    name: str = Field(min_length=1, max_length=100)
    role: str = Field(pattern="^(protagonist|antagonist|supporting|background)$")
    description: str = Field(min_length=1)


class CharacterCreate(CharacterBase):
    """Schema for character creation."""

    appearance: CharacterAppearanceSchema
    personality: CharacterPersonalitySchema
    reference_image_url: Optional[str] = None
    style_notes: Optional[str] = None


class CharacterUpdate(BaseModel):
    """Schema for character updates."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, pattern="^(protagonist|antagonist|supporting|background)$")
    description: Optional[str] = Field(None, min_length=1)
    appearance: Optional[CharacterAppearanceSchema] = None
    personality: Optional[CharacterPersonalitySchema] = None
    reference_image_url: Optional[str] = None
    style_notes: Optional[str] = None


class CharacterResponse(BaseEntitySchema):
    """Schema for character response."""

    project_id: UUID
    name: str
    role: str
    description: str
    appearance: CharacterAppearanceSchema
    personality: CharacterPersonalitySchema
    reference_image_url: Optional[str]
    style_notes: Optional[str]
    relationships: Dict[UUID, str]
