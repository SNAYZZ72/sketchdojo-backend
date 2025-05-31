# =============================================================================
# app/core/security.py - NEW SECURITY CONFIGURATION
# =============================================================================
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SecuritySettings(BaseModel):
    """Security configuration settings."""

    # JWT Settings
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password Requirements
    min_password_length: int = 8
    max_password_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special_chars: bool = True
    password_history_length: int = 5  # Remember last 5 passwords

    # Account Lockout
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    enable_account_lockout: bool = True

    # Rate Limiting
    auth_rate_limit_per_minute: int = 5
    login_rate_limit_per_minute: int = 3
    register_rate_limit_per_hour: int = 2
    password_reset_rate_limit_per_hour: int = 3

    # Session Management
    enable_concurrent_sessions: bool = True
    max_concurrent_sessions: int = 5

    # Security Headers
    enable_security_headers: bool = True
    hsts_max_age: int = 31536000  # 1 year

    # CORS Settings
    cors_allow_credentials: bool = True
    cors_allow_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Email Verification
    require_email_verification: bool = True
    email_verification_expire_hours: int = 24

    # Password Reset
    password_reset_expire_hours: int = 1
    password_reset_token_length: int = 32

    # Audit Logging
    enable_audit_logging: bool = True
    log_failed_attempts: bool = True
    log_successful_logins: bool = True
    log_password_changes: bool = True

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v

    @field_validator('cors_allow_origins')
    @classmethod
    def validate_cors_origins(cls, v: list) -> list:
        # In production, ensure no wildcard origins
        if "*" in v and len(v) > 1:
            raise ValueError('Cannot mix wildcard with specific origins')
        return v


def generate_secure_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_security_headers() -> dict:
    """Get security headers for HTTP responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; img-src 'self' https://fastapi.tiangolo.com data:; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }


class SecurityMiddleware:
    """Security middleware for adding security headers."""

    def __init__(self, app, settings: SecuritySettings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start" and self.settings.enable_security_headers:
                headers = dict(message.get("headers", []))
                security_headers = get_security_headers()

                for key, value in security_headers.items():
                    headers[key.encode()] = value.encode()

                message["headers"] = list(headers.items())

            await send(message)

        await self.app(scope, receive, send_wrapper)