# =============================================================================
# app/schemas/auth.py
# =============================================================================
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Token(BaseModel):
    """Basic token schema."""
    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Complete token response schema."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry time in seconds")


class RefreshToken(BaseModel):
    """Refresh token request schema."""
    refresh_token: str = Field(..., description="Valid refresh token", min_length=1)

    @field_validator('refresh_token')
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Refresh token cannot be empty')
        return v.strip()


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    verified: bool = Field(default=False, description="Email verification status")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: str = Field(..., description="Token type (access/refresh)")
    jti: str = Field(..., description="JWT ID for blacklisting")


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str = Field(..., description="Current password", min_length=1)
    new_password: str = Field(..., description="New password", min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""
    email: str = Field(..., description="Email address", max_length=255)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.lower().strip()
        if not v:
            raise ValueError('Email cannot be empty')
        # Basic email validation (FastAPI EmailStr would be better)
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""
    reset_token: str = Field(..., description="Password reset token", min_length=1)
    new_password: str = Field(..., description="New password", min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    verification_token: str = Field(..., description="Email verification token", min_length=1)


class AuthStatusResponse(BaseModel):
    """Authentication status response."""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    email: Optional[str] = Field(None, description="User email if authenticated")
    role: Optional[str] = Field(None, description="User role if authenticated")
    verified: Optional[bool] = Field(None, description="Email verification status")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")
    logout_all_devices: bool = Field(default=False, description="Logout from all devices")


class LoginAttempt(BaseModel):
    """Login attempt tracking schema."""
    email_or_username: str = Field(..., description="Email or username used")
    success: bool = Field(..., description="Whether login was successful")
    ip_address: str = Field(..., description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Attempt timestamp")
    failure_reason: Optional[str] = Field(None, description="Reason for failure if applicable")


class SecurityEvent(BaseModel):
    """Security event schema for audit logging."""
    event_type: str = Field(..., description="Type of security event")
    user_id: Optional[str] = Field(None, description="User ID if applicable")
    ip_address: str = Field(..., description="Client IP address")
    details: dict = Field(default_factory=dict, description="Additional event details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event timestamp")
    severity: str = Field(default="info", description="Event severity level")


class RateLimitStatus(BaseModel):
    """Rate limit status schema."""
    limit: int = Field(..., description="Request limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="When limit resets")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")


class AuthHealthResponse(BaseModel):
    """Auth service health response."""
    status: str = Field(..., description="Service status")
    service: str = Field(default="authentication", description="Service name")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Health check time")
    database_status: Optional[str] = Field(None, description="Database connection status")
    redis_status: Optional[str] = Field(None, description="Redis connection status")