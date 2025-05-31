# =============================================================================
# app/infrastructure/database/models/character.py
# =============================================================================
from sqlalchemy import JSON, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class CharacterModel(BaseModel):
    """Character database model."""

    __tablename__ = "characters"

    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # protagonist, antagonist, etc.
    description = Column(Text, nullable=False)

    # JSON fields for complex data
    appearance = Column(JSON, nullable=False)  # CharacterAppearance data
    personality = Column(JSON, nullable=False)  # CharacterPersonality data
    relationships = Column(JSON, nullable=True)  # character_id -> relationship mapping

    # Visual consistency
    reference_image_url = Column(String(500), nullable=True)
    style_notes = Column(Text, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="characters")
