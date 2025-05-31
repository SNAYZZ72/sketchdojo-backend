# =============================================================================
# app/infrastructure/database/models/webtoon.py
# =============================================================================
from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.domain.models.webtoon import WebtoonStatus

from .base import BaseModel


class WebtoonModel(BaseModel):
    """Webtoon database model."""

    __tablename__ = "webtoons"

    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(WebtoonStatus), default=WebtoonStatus.PLANNING, nullable=False)

    # Metadata stored as JSON
    webtoon_metadata = Column(JSON, nullable=False)  # WebtoonMetadata data

    # Content structure
    story_summary = Column(Text, nullable=True)
    panel_count = Column(Integer, default=0, nullable=False)
    estimated_panels = Column(Integer, default=6, nullable=False)

    # Visual consistency
    art_style_reference = Column(String(500), nullable=True)
    style_notes = Column(Text, nullable=True)
    color_palette = Column(JSON, nullable=True)  # List of color codes

    # Publication
    thumbnail_url = Column(String(500), nullable=True)
    published_url = Column(String(500), nullable=True)
    view_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)

    # Relationships
    project = relationship("ProjectModel", back_populates="webtoons")
    panels = relationship("PanelModel", back_populates="webtoon", cascade="all, delete-orphan")
