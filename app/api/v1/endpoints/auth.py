# =============================================================================
# app/api/v1/endpoints/auth.py
# =============================================================================
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    auth_rate_limit,
    get_current_active_user,
    get_current_user,
    login_rate_limit,
    register_rate_limit,
)
from app.domain.services.auth_service import AuthService
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.schemas.auth import RefreshToken, TokenResponse
from app.schemas.user import UserCreate, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get auth service instance."""
    user_repo = UserRepository(db)
    return AuthService(user_repo)


@router.post("/register",
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(register_rate_limit)])
async def register(
        user_data: UserCreate,
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.

    - **email**: Valid email address (will be normalized to lowercase)
    - **username**: Unique username (3-50 characters, alphanumeric + underscore)
    - **password**: Strong password (min 8 chars, must include upper, lower, digit, special char)

    Returns the created user information (without password).
    """
    try:
        logger.info(f"Registration attempt from IP: {request.client.host}")
        user = await auth_service.register_user(user_data)
        logger.info(f"User registered successfully: {user.email}")
        return user

    except ValueError as e:
        logger.warning(f"Registration failed for {user_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login",
             response_model=TokenResponse,
             dependencies=[Depends(login_rate_limit)])
async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email/username and password.

    - **username**: Email address or username
    - **password**: User password

    Returns access token and refresh token for API authentication.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Login attempt for {form_data.username} from IP: {client_ip}")

        tokens = await auth_service.authenticate_user(
            form_data.username,
            form_data.password
        )

        logger.info(f"Login successful for: {form_data.username}")
        return tokens

    except ValueError as e:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(f"Login failed for {form_data.username} from {client_ip}: {str(e)}")

        # Always return the same error message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/refresh",
             response_model=TokenResponse,
             dependencies=[Depends(auth_rate_limit)])
async def refresh_token(
        refresh_data: RefreshToken,
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token and refresh token.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Token refresh attempt from IP: {client_ip}")

        tokens = await auth_service.refresh_tokens(refresh_data.refresh_token)

        logger.info("Token refresh successful")
        return tokens

    except ValueError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.

    Requires valid access token in Authorization header.
    """
    return current_user


@router.post("/logout", dependencies=[Depends(auth_rate_limit)])
async def logout(
        request: Request,
        refresh_data: Optional[RefreshToken] = None,
        current_user: UserResponse = Depends(get_current_user),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user by invalidating tokens.

    - **refresh_token**: Optional refresh token to invalidate

    Blacklists the current access token and optional refresh token.
    """
    try:
        # Extract access token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        access_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

        refresh_token = refresh_data.refresh_token if refresh_data else None

        await auth_service.logout_user(access_token, refresh_token)

        logger.info(f"User logged out successfully: {current_user.email}")
        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Don't fail logout even if blacklisting fails
        return {"message": "Logout completed"}


@router.post("/change-password", dependencies=[Depends(auth_rate_limit)])
async def change_password(
        current_password: str,
        new_password: str,
        current_user: UserResponse = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password.

    - **current_password**: Current password for verification
    - **new_password**: New password (must meet strength requirements)

    Requires authentication.
    """
    try:
        await auth_service.change_password(
            current_user.id,
            current_password,
            new_password
        )

        logger.info(f"Password changed for user: {current_user.email}")
        return {"message": "Password changed successfully"}

    except ValueError as e:
        logger.warning(f"Password change failed for {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again."
        )


@router.post("/forgot-password", dependencies=[Depends(auth_rate_limit)])
async def forgot_password(
        email: str,
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset.

    - **email**: Email address of the account

    Sends password reset email if account exists.
    Always returns success to prevent email enumeration.
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Password reset requested for {email} from IP: {client_ip}")

        reset_token = await auth_service.reset_password_request(email)

        # In a real application, you would send an email here
        # For now, we'll just log the token (REMOVE IN PRODUCTION)
        if reset_token != "reset_token_placeholder":
            logger.info(f"Password reset token generated: {reset_token[:20]}...")

        # Always return success message to prevent email enumeration
        return {
            "message": "If an account with this email exists, a password reset link has been sent."
        }

    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        # Still return success to prevent information disclosure
        return {
            "message": "If an account with this email exists, a password reset link has been sent."
        }


@router.post("/reset-password", dependencies=[Depends(auth_rate_limit)])
async def reset_password(
        reset_token: str,
        new_password: str,
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using reset token.

    - **reset_token**: Password reset token from email
    - **new_password**: New password (must meet strength requirements)
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Password reset attempt from IP: {client_ip}")

        await auth_service.reset_password(reset_token, new_password)

        logger.info("Password reset completed successfully")
        return {"message": "Password reset successfully"}

    except ValueError as e:
        logger.warning(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )


@router.post("/verify-email")
async def verify_email(
        verification_token: str,
        auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify email address using verification token.

    - **verification_token**: Email verification token
    """
    # This would be implemented similar to password reset
    # but for email verification
    return {"message": "Email verification not yet implemented"}


@router.get("/health")
async def auth_health():
    """Health check for auth service."""
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": "2024-01-15T10:30:00Z"
    }