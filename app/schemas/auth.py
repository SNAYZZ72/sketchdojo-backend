# =============================================================================
# app/schemas/auth.py
# =============================================================================
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token schema."""

    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str  # subject (user id)
    exp: int  # expiration time
    type: str  # token type (access or refresh)
    fresh: bool = False


class RefreshToken(BaseModel):
    """Refresh token schema."""

    refresh_token: str
