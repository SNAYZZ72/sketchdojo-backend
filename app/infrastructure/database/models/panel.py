# =============================================================================
# app/infrastructure/database/models/panel.py
# =============================================================================
from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.models.panel import PanelLayout, PanelSize, PanelStatus

from .base import BaseModel


class PanelModel(BaseModel):
    """Panel database model."""

    __tablename__ = "panels"

    webtoon_id = Column(String(36), ForeignKey("webtoons.id"), nullable=False, index=True)
    scene_id = Column(String(36), ForeignKey("scenes.id"), nullable=True, index=True)
    sequence_number = Column(Integer, default=0, nullable=False)

    # Visual properties
    size = Column(SQLEnum(PanelSize), default=PanelSize.MEDIUM, nullable=False)
    layout = Column(SQLEnum(PanelLayout), default=PanelLayout.LANDSCAPE, nullable=False)
    status = Column(SQLEnum(PanelStatus), default=PanelStatus.DRAFT, nullable=False)

    # Content
    visual_description = Column(Text, nullable=False)
    characters_present = Column(JSON, nullable=True)  # List of character UUIDs
    speech_bubbles = Column(JSON, nullable=True)  # List of SpeechBubble data
    visual_elements = Column(JSON, nullable=True)  # List of VisualElement data

    # Generation data
    ai_prompt = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    generation_metadata = Column(JSON, nullable=True)

    # Review and feedback
    feedback = Column(Text, nullable=True)
    revision_notes = Column(Text, nullable=True)

    # Relationships
    webtoon = relationship("WebtoonModel", back_populates="panels")
    scene = relationship("SceneModel", back_populates="panels")
