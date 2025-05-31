# =============================================================================
# app/domain/services/auth_service.py
# =============================================================================
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.domain.models.user import User, UserRole, UserStatus
from app.domain.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization service."""

    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    def _create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        existing_username = await self.user_repo.get_by_username(user_data.username)
        if existing_username:
            raise ValueError("Username already taken")

        # Create user domain object
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=self._hash_password(user_data.password),
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_verified=False,  # Would require email verification in production
        )

        # Save to repository
        saved_user = await self.user_repo.create(user)

        logger.info(f"User registered: {saved_user.email}")
        return UserResponse.from_orm(saved_user)

    async def authenticate_user(self, email_or_username: str, password: str) -> TokenResponse:
        """Authenticate user and return tokens."""
        # Try to find user by email first, then username
        user = await self.user_repo.get_by_email(email_or_username)
        if not user:
            user = await self.user_repo.get_by_username(email_or_username)

        if not user or not self._verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        if user.status != UserStatus.ACTIVE:
            raise ValueError("Account is not active")

        # Create tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = self._create_access_token(token_data)
        refresh_token = self._create_refresh_token(token_data)

        logger.info(f"User authenticated: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, user_id: UUID) -> TokenResponse:
        """Refresh user tokens."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise ValueError("Invalid user")

        # Create new tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = self._create_access_token(token_data)
        refresh_token = self._create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def logout_user(self, user_id: UUID):
        """Logout user (in production, would invalidate tokens)."""
        # In a production system, you would:
        # 1. Add tokens to a blacklist in Redis
        # 2. Or use short-lived tokens with token rotation
        # 3. Or implement proper session management
        logger.info(f"User logged out: {user_id}")
