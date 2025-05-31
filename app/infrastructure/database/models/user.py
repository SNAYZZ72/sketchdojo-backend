# =============================================================================
# app/infrastructure/database/models/user.py
# =============================================================================
from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import relationship

from app.domain.models.user import UserRole, UserStatus

from .base import BaseModel


class UserModel(BaseModel):
    """User database model."""

    __tablename__ = "users"

    email = Column(String(191), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    profile_image_url = Column(String(500), nullable=True)

    # Subscription and limits
    max_projects = Column(Integer, default=5, nullable=False)
    max_panels_per_webtoon = Column(Integer, default=10, nullable=False)
    monthly_generation_limit = Column(Integer, default=100, nullable=False)
    current_month_generations = Column(Integer, default=0, nullable=False)

    # Relationships
    projects = relationship("ProjectModel", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="user", cascade="all, delete-orphan")
