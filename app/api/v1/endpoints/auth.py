# =============================================================================
# app/api/v1/endpoints/auth.py
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user
from app.domain.services.auth_service import AuthService
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    try:
        user = await auth_service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Login user and return access token."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    try:
        tokens = await auth_service.authenticate_user(
            form_data.username, form_data.password  # Can be email or username
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Refresh access token."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    tokens = await auth_service.refresh_tokens(current_user.id)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(
    current_user: UserResponse = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Logout user (invalidate tokens)."""
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    await auth_service.logout_user(current_user.id)
    return {"message": "Successfully logged out"}
