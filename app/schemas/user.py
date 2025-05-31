# =============================================================================
# app/schemas/user.py
# =============================================================================
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.domain.models.user import UserRole, UserStatus

from .base import BaseEntitySchema


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    profile_image_url: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseEntitySchema):
    """Schema for user response."""

    email: EmailStr
    username: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    profile_image_url: Optional[str] = None
    max_projects: int
    max_panels_per_webtoon: int
    monthly_generation_limit: int
    current_month_generations: int


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
