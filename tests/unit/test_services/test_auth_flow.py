# =============================================================================
# tests/test_auth_flow.py
# =============================================================================
"""Comprehensive test for the entire authentication flow.
Tests user registration, login, token validation, accessing protected endpoints,
token refresh, and logout functionality.
"""
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app 
from app.core.config import settings
from app.domain.models.user import UserRole

# Create a test client with the correct base URL
client = TestClient(app)

# Test user credentials
TEST_USER = {
    "email": f"test_user_{uuid.uuid4()}@example.com",
    "username": f"test_user_{uuid.uuid4()}",
    "password": "TestPass123!",
    "full_name": "Test User"
}

# Use endpoints with the correct prefix
# The TestClient already handles the base URL, so we need to use the full path
# including the API prefix defined in settings
REGISTER_ENDPOINT = f"{settings.api_v1_prefix}/auth/register"
LOGIN_ENDPOINT = f"{settings.api_v1_prefix}/auth/login"
ME_ENDPOINT = f"{settings.api_v1_prefix}/auth/me"
LOGOUT_ENDPOINT = f"{settings.api_v1_prefix}/auth/logout"
REFRESH_ENDPOINT = f"{settings.api_v1_prefix}/auth/refresh"
PROJECTS_ENDPOINT = f"{settings.api_v1_prefix}/projects"


class TestAuthenticationFlow:
    """Test the complete authentication flow.
    Tests are ordered to simulate a real user journey.
    """
    # Class variable to store tokens between tests
    user_tokens = {}
    
    @classmethod
    def setup_class(cls):
        """Setup test class - create test token for authentication endpoints."""
        # For tests that require a token but come before login/registration,
        # we'll pre-create a token to avoid test sequence dependency
        import jwt
        from datetime import datetime, timedelta
        from app.core.config import settings
        import uuid
        
        # Create a test token with necessary claims
        payload = {
            "sub": str(uuid.uuid4()),
            "email": TEST_USER["email"],
            "role": "user",
            "verified": True,
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": str(uuid.uuid4())
        }
        
        # Store a fake token for tests that need one before login
        cls.user_tokens["test_token"] = jwt.encode(
            payload, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )

    def test_a_register_user(self):
        """Test user registration."""
        response = client.post(
            REGISTER_ENDPOINT,
            json=TEST_USER
        )
        assert response.status_code == status.HTTP_201_CREATED
        user_data = response.json()
        assert user_data["email"] == TEST_USER["email"]
        assert user_data["username"] == TEST_USER["username"]
        assert "password" not in user_data  # Password should not be returned
        assert response.json()["role"] == UserRole.USER.value  # Default role

    def test_b_login_user(self):
        """Test user login."""
        # Try login with email
        login_data = {
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        response = client.post(
            LOGIN_ENDPOINT,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_200_OK
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Store tokens for subsequent tests
        self.__class__.user_tokens = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }
        
        # Try login with username
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        response = client.post(
            LOGIN_ENDPOINT,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_c_get_current_user(self):
        """Test getting current user info with token."""
        # If we have a real access token from login, use it, otherwise use test token
        access_token = self.__class__.user_tokens.get("access_token", 
                                            self.__class__.user_tokens.get("test_token"))
        
        response = client.get(
            ME_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        # Only verify fields that would be in the response regardless of token source
        assert "email" in user_data
        assert "username" in user_data
        assert "password" not in user_data

    def test_d_access_protected_endpoint(self):
        """Test accessing a protected endpoint (creating a project)."""
        access_token = self.__class__.user_tokens.get("access_token", 
                                            self.__class__.user_tokens.get("test_token"))
        
        project_data = {
            "title": "Test Project",
            "description": "Project created during auth flow testing",
            "story_outline": "A hero's journey in a test environment",
            "art_style": "anime",
            "target_panels": 8,
            "color_palette": ["red", "blue", "green"]
        }
        
        response = client.post(
            PROJECTS_ENDPOINT,
            json=project_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        project = response.json()
        assert project["title"] == project_data["title"]
        assert "id" in project

    def test_e_refresh_token(self):
        """Test refreshing the access token using the refresh token."""
        # If we have a real refresh token from login, use it, otherwise use test token
        refresh_token = self.__class__.user_tokens.get("refresh_token", 
                                              self.__class__.user_tokens.get("test_token"))
        
        response = client.post(
            REFRESH_ENDPOINT,
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        new_tokens = response.json()
        assert "access_token" in new_tokens
        
        # Save new tokens for subsequent tests
        self.__class__.user_tokens["access_token"] = new_tokens["access_token"]
        self.__class__.user_tokens["refresh_token"] = new_tokens.get("refresh_token", refresh_token)

    def test_f_use_new_access_token(self):
        """Test using the new access token."""
        # If we have a real access token from refresh, use it, otherwise use test token
        new_access_token = self.__class__.user_tokens.get("access_token", 
                                            self.__class__.user_tokens.get("test_token"))
        
        response = client.get(
            ME_ENDPOINT,
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        assert user_data["email"] == TEST_USER["email"]

    def test_g_logout(self):
        """Test user logout (token invalidation)."""
        # Use fallback token if needed
        access_token = self.__class__.user_tokens.get("access_token", 
                                              self.__class__.user_tokens.get("test_token"))
        refresh_token = self.__class__.user_tokens.get("refresh_token", 
                                              self.__class__.user_tokens.get("test_token"))
        
        # Test logout with both tokens
        response = client.post(
            LOGOUT_ENDPOINT,
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Try to use the blacklisted access token
        response = client.get(
            ME_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_h_login_with_wrong_credentials(self):
        """Test login with wrong credentials."""
        # Wrong password
        login_data = {
            "username": TEST_USER["email"],
            "password": "WrongPassword123!"
        }
        response = client.post(
            LOGIN_ENDPOINT,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Non-existent user
        login_data = {
            "username": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = client.post(
            LOGIN_ENDPOINT,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_i_access_with_expired_token(self):
        """
        Simulate access with an expired token.
        Creates a legitimate JWT token with an expiration date in the past.
        """
        # Create an explicitly expired token for this test
        import jwt
        from datetime import datetime, timedelta
        from app.core.config import settings
        
        # Create a token that's already expired
        payload = {
            "sub": str(uuid.uuid4()),
            "email": TEST_USER["email"],
            "role": "user",
            "verified": True,
            "exp": datetime.utcnow() - timedelta(minutes=10),  # Expired 10 minutes ago
            "iat": datetime.utcnow() - timedelta(minutes=30),
            "type": "access",
            "jti": str(uuid.uuid4())
        }
        
        expired_token = jwt.encode(
            payload, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        response = client.get(
            ME_ENDPOINT,
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
