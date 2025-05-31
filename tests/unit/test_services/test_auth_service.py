# =============================================================================
# tests/unit/test_services/test_auth_service.py
# =============================================================================
from unittest.mock import AsyncMock

import pytest

from app.domain.services.auth_service import AuthService
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration."""
    # Mock repository
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None
    user_repo.get_by_username.return_value = None
    user_repo.create.return_value = AsyncMock(
        id="test-id", email="test@example.com", username="testuser"
    )

    # Create service
    auth_service = AuthService(user_repo)

    # Test registration
    user_data = UserCreate(
        email="test@example.com", username="testuser", password="TestPassword123"
    )

    result = await auth_service.register_user(user_data)

    assert result.email == "test@example.com"
    assert result.username == "testuser"
    user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_duplicate_email():
    """Test registration with duplicate email."""
    # Mock repository
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = AsyncMock()  # Existing user

    # Create service
    auth_service = AuthService(user_repo)

    # Test registration
    user_data = UserCreate(
        email="test@example.com", username="testuser", password="TestPassword123"
    )

    with pytest.raises(ValueError, match="User with this email already exists"):
        await auth_service.register_user(user_data)
