# =============================================================================
# app/domain/services/auth_service.py
# =============================================================================
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set
import uuid
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
import redis.asyncio as redis

from app.core.config import settings
from app.domain.models.user import User, UserRole, UserStatus
from app.domain.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)

# Password hashing context with stronger settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)


class AuthService:
    """Secure authentication and authorization service."""

    def __init__(self, user_repository: UserRepository, redis_client: Optional[redis.Redis] = None):
        self.user_repo = user_repository
        self.redis = redis_client or redis.from_url(settings.redis_url)

    def _hash_password(self, password: str) -> str:
        """Hash a password with bcrypt."""
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def _validate_password_strength(self, password: str) -> None:
        """Validate password meets security requirements."""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = {'password', '12345678', 'qwerty123', 'admin123'}
        if password.lower() in weak_passwords:
            errors.append("Password is too common and easily guessable")

        if errors:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")

    def _create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": now,
            "type": "access",
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        })

        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    def _create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        now = datetime.now(timezone.utc)
        to_encode = {
            "sub": user_id,
            "exp": now + timedelta(days=settings.refresh_token_expire_days),
            "iat": now,
            "type": "refresh",
            "jti": str(uuid.uuid4())
        }

        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    async def _blacklist_token(self, token: str) -> None:
        """Add token to blacklist."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                # Store blacklisted token until expiration
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    await self.redis.setex(f"blacklist:{jti}", int(ttl), "1")
        except JWTError:
            pass  # Invalid token, ignore

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        try:
            result = await self.redis.get(f"blacklist:{jti}")
            return result is not None
        except Exception:
            return False

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user with comprehensive validation."""

        # Validate password strength
        self._validate_password_strength(user_data.password)

        # Check for existing users
        existing_user = await self.user_repo.get_by_email(user_data.email.lower())
        if existing_user:
            raise ValueError("An account with this email address already exists")

        existing_username = await self.user_repo.get_by_username(user_data.username.lower())
        if existing_username:
            raise ValueError("This username is already taken")

        # Create user domain object
        user = User(
            email=user_data.email.lower().strip(),
            username=user_data.username.lower().strip(),
            hashed_password=self._hash_password(user_data.password),
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_verified=False  # Email verification required
        )

        # Save to repository
        try:
            saved_user = await self.user_repo.create(user)
            logger.info(f"User registered successfully: {saved_user.email}")
            return UserResponse.model_validate(saved_user)
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise ValueError("Registration failed. Please try again.")

    async def authenticate_user(self, email_or_username: str, password: str) -> TokenResponse:
        """Authenticate user and return secure tokens."""

        if not email_or_username or not password:
            raise ValueError("Email/username and password are required")

        # Normalize input
        identifier = email_or_username.lower().strip()

        # Try to find user by email first, then username
        user = await self.user_repo.get_by_email(identifier)
        if not user:
            user = await self.user_repo.get_by_username(identifier)

        # Always hash the password even if user not found (timing attack prevention)
        password_verified = False
        if user:
            password_verified = self._verify_password(password, user.hashed_password)
        else:
            # Dummy hash to prevent timing attacks
            self._verify_password(password, "$2b$12$dummy.hash.to.prevent.timing.attacks")

        if not user or not password_verified:
            logger.warning(f"Failed authentication attempt for: {identifier}")
            raise ValueError("Invalid email/username or password")

        if user.status != UserStatus.ACTIVE:
            raise ValueError("Account is suspended or inactive")

        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "verified": user.is_verified
        }

        access_token = self._create_access_token(token_data)
        refresh_token = self._create_refresh_token(str(user.id))

        # Update last login
        await self.user_repo.update_last_login(user.id)

        logger.info(f"User authenticated successfully: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])

            # Validate token type and check blacklist
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")

            jti = payload.get("jti")
            if jti and await self._is_token_blacklisted(jti):
                raise ValueError("Token has been revoked")

            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")

        except JWTError:
            raise ValueError("Invalid or expired refresh token")

        # Get user and validate status
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or user.status != UserStatus.ACTIVE:
            raise ValueError("User account is invalid or inactive")

        # Blacklist old refresh token
        await self._blacklist_token(refresh_token)

        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "verified": user.is_verified
        }

        new_access_token = self._create_access_token(token_data)
        new_refresh_token = self._create_refresh_token(str(user.id))

        logger.info(f"Tokens refreshed for user: {user.email}")

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def logout_user(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Logout user by blacklisting tokens."""
        try:
            # Blacklist access token
            await self._blacklist_token(access_token)

            # Blacklist refresh token if provided
            if refresh_token:
                await self._blacklist_token(refresh_token)

            logger.info("User logged out successfully")

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            # Don't raise exception for logout failures

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and await self._is_token_blacklisted(jti):
                raise ValueError("Token has been revoked")

            # Validate token type
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")

            return payload

        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        """Change user password with validation."""

        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not self._verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        # Validate new password
        self._validate_password_strength(new_password)

        # Check if new password is different
        if self._verify_password(new_password, user.hashed_password):
            raise ValueError("New password must be different from current password")

        # Update password
        user.hashed_password = self._hash_password(new_password)
        await self.user_repo.update(user)

        logger.info(f"Password changed for user: {user.email}")

    async def reset_password_request(self, email: str) -> str:
        """Request password reset (returns reset token)."""
        user = await self.user_repo.get_by_email(email.lower())
        if not user:
            # Don't reveal if email exists
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return "reset_token_placeholder"  # Return fake token

        # Create reset token
        reset_data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1),  # 1 hour expiry
            "iat": datetime.utcnow(),
            "jti": str(UUID.uuid4())
        }

        reset_token = jwt.encode(reset_data, settings.secret_key, algorithm=settings.algorithm)

        # Store reset token in Redis with expiration
        await self.redis.setex(f"reset:{user.id}", 3600, reset_token)

        logger.info(f"Password reset requested for: {user.email}")
        return reset_token

    async def reset_password(self, reset_token: str, new_password: str) -> None:
        """Reset password using reset token."""
        try:
            payload = jwt.decode(reset_token, settings.secret_key, algorithms=[settings.algorithm])

            if payload.get("type") != "password_reset":
                raise ValueError("Invalid token type")

            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")

            # Verify token is still valid in Redis
            stored_token = await self.redis.get(f"reset:{user_id}")
            if not stored_token or stored_token.decode() != reset_token:
                raise ValueError("Reset token is invalid or expired")

        except JWTError:
            raise ValueError("Invalid or expired reset token")

        # Get user and validate
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user:
            raise ValueError("User not found")

        # Validate new password
        self._validate_password_strength(new_password)

        # Update password
        user.hashed_password = self._hash_password(new_password)
        await self.user_repo.update(user)

        # Remove reset token
        await self.redis.delete(f"reset:{user_id}")

        logger.info(f"Password reset completed for: {user.email}")