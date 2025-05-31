# =============================================================================
# app/infrastructure/database/models/scene.py
# =============================================================================
from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.models.scene import SceneType, TimeOfDay

from .base import BaseModel


class SceneModel(BaseModel):
    """Scene database model."""

    __tablename__ = "scenes"

    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    scene_type = Column(SQLEnum(SceneType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Environment data stored as JSON
    environment = Column(JSON, nullable=False)  # SceneEnvironment data

    # Content stored as JSON arrays
    characters_present = Column(JSON, nullable=True)  # List of character UUIDs
    dialogue_lines = Column(JSON, nullable=True)  # List of DialogueLine data
    emotional_beats = Column(JSON, nullable=True)  # List of strings
    special_effects = Column(JSON, nullable=True)  # List of strings

    # Action and visual direction
    action_description = Column(Text, nullable=True)
    camera_angle = Column(String(50), default="medium", nullable=False)
    visual_focus = Column(String(200), nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="scenes")
    panels = relationship("PanelModel", back_populates="scene")
