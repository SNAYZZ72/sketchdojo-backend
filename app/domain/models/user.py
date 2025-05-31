# =============================================================================
# app/domain/models/user.py
# =============================================================================
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from .base import DomainEntity


class UserRole(str, Enum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class User(DomainEntity):
    """User domain model."""

    # User specific required fields
    email: str
    username: str
    hashed_password: str
    
    # Fields from DomainEntity that need to be explicitly included in the dataclass
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Fields with default values
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False
    profile_image_url: Optional[str] = None

    # Subscription and limits
    max_projects: int = 5
    max_panels_per_webtoon: int = 10
    monthly_generation_limit: int = 100
    current_month_generations: int = 0

    def can_create_project(self) -> bool:
        """Check if user can create a new project."""
        return self.status == UserStatus.ACTIVE and self.is_verified

    def can_generate_panel(self) -> bool:
        """Check if user can generate a new panel."""
        return (
            self.status == UserStatus.ACTIVE
            and self.current_month_generations < self.monthly_generation_limit
        )

    def increment_generations(self) -> None:
        """Increment the monthly generation count."""
        self.current_month_generations += 1

    def reset_monthly_generations(self) -> None:
        """Reset monthly generation count (called monthly)."""
        self.current_month_generations = 0
