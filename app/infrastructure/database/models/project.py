# =============================================================================
# app/infrastructure/database/models/project.py
# =============================================================================
from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.models.project import ProjectStatus

from .base import BaseModel


class ProjectModel(BaseModel):
    """Project database model."""

    __tablename__ = "projects"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    project_metadata = Column(JSON, nullable=True)

    # Content structure
    story_outline = Column(Text, nullable=True)
    target_panels = Column(Integer, default=6, nullable=False)
    art_style = Column(String(50), default="webtoon", nullable=False)
    color_palette = Column(JSON, nullable=True)  # List of color codes

    # Relationships
    user = relationship("UserModel", back_populates="projects")
    webtoons = relationship("WebtoonModel", back_populates="project", cascade="all, delete-orphan")
    characters = relationship(
        "CharacterModel", back_populates="project", cascade="all, delete-orphan"
    )
    scenes = relationship("SceneModel", back_populates="project", cascade="all, delete-orphan")
