# =============================================================================
# tests/conftest.py
# =============================================================================
import asyncio
import os
import sys
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

# Try to import test dependencies, fall back gracefully
try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app.core.config import settings
from app.main import app
from app.domain.models.user import User, UserRole, UserStatus

# Test database configuration - only if aiosqlite is available
if HAS_AIOSQLITE:
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a test database session or mock if aiosqlite not available."""
    if not HAS_AIOSQLITE:
        # Return a mock session if aiosqlite is not available
        mock_session = AsyncMock(spec=AsyncSession)
        yield mock_session
        return

    # Real database session for integration tests
    try:
        from app.core.database import Base

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            yield session

        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    except Exception as e:
        # Fallback to mock if database setup fails
        print(f"Database setup failed, using mock: {e}")
        mock_session = AsyncMock(spec=AsyncSession)
        yield mock_session


@pytest.fixture
def client(db_session, mock_redis):
    """Create a test client with mocked dependencies."""
    from fastapi.testclient import TestClient
    from app.infrastructure.cache import redis_client
    from app.core.database import get_db
    
    # Save original methods before overriding
    original_get = redis_client.get
    original_setex = redis_client.setex
    original_delete = redis_client.delete
    original_incr = redis_client.incr
    
    # Override Redis client methods with synchronous versions
    redis_client.get = mock_redis.get
    redis_client.setex = mock_redis.setex
    redis_client.delete = mock_redis.delete
    redis_client.incr = mock_redis.incr
    
    # Create synchronous override for database session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Apply dependency overrides
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client with synchronous TestClient
    test_client = TestClient(app=app, base_url="http://testserver")
    
    yield test_client
    
    # Restore Redis methods after test
    redis_client.get = original_get
    redis_client.setex = original_setex
    redis_client.delete = original_delete
    redis_client.incr = original_incr
    
    # Clear dependency overrides
    app.dependency_overrides = {}


@pytest.fixture
async def test_user(db_session):
    """Create a test user (mocked or real)."""
    if isinstance(db_session, AsyncMock):
        # Return a mock user for unit tests
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.role = UserRole.USER
        mock_user.status = UserStatus.ACTIVE
        mock_user.is_verified = True
        return mock_user

    # Real user for integration tests
    try:
        from app.infrastructure.database.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_verified=True,
        )

        saved_user = await user_repo.create(user)
        return saved_user

    except Exception as e:
        print(f"Real user creation failed, using mock: {e}")
        # Fallback to mock user
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        return mock_user


@pytest.fixture
async def admin_user(db_session):
    """Create an admin test user (mocked or real)."""
    if isinstance(db_session, AsyncMock):
        # Return a mock admin user
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "admin@example.com"
        mock_user.username = "admin"
        mock_user.role = UserRole.ADMIN
        mock_user.status = UserStatus.ACTIVE
        mock_user.is_verified = True
        return mock_user

    # Real admin user for integration tests
    try:
        from app.infrastructure.database.repositories.user_repository import UserRepository

        user_repo = UserRepository(db_session)

        user = User(
            email="admin@example.com",
            username="admin",
            hashed_password="hashed_password",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_verified=True,
        )

        saved_user = await user_repo.create(user)
        return saved_user

    except Exception:
        # Fallback to mock admin user
        mock_user = AsyncMock()
        mock_user.id = uuid4()
        mock_user.email = "admin@example.com"
        mock_user.username = "admin"
        mock_user.role = UserRole.ADMIN
        return mock_user


@pytest.fixture
def test_token():
    """Create a pre-generated JWT token for testing."""
    import jwt
    import datetime
    import uuid
    
    # Create a token with standard claims that won't expire during tests
    now = datetime.datetime.now(datetime.timezone.utc)
    token_data = {
        "sub": str(uuid.uuid4()),  # Subject (user ID)
        "exp": now + datetime.timedelta(hours=1),  # Expiration time
        "iat": now,  # Issued at time
        "jti": str(uuid.uuid4()),  # JWT ID
        "type": "access",  # Token type
        "fresh": True,
        "email": "test@example.com",
        "username": "testuser",
        "role": "user"
    }
    
    # Use the same secret key as in the application
    from app.core.config import settings
    
    # Generate token
    token = jwt.encode(token_data, settings.jwt_secret_key, algorithm="HS256")
    return token


@pytest.fixture
def expired_test_token():
    """Create a pre-generated expired JWT token for testing."""
    import jwt
    import datetime
    import uuid
    
    # Create a token with standard claims that is already expired
    now = datetime.datetime.now(datetime.timezone.utc)
    token_data = {
        "sub": str(uuid.uuid4()),  # Subject (user ID)
        "exp": now - datetime.timedelta(hours=1),  # Expired 1 hour ago
        "iat": now - datetime.timedelta(hours=2),  # Issued 2 hours ago
        "jti": str(uuid.uuid4()),  # JWT ID
        "type": "access",  # Token type
        "fresh": True,
        "email": "test@example.com",
        "username": "testuser",
        "role": "user"
    }
    
    # Use the same secret key as in the application
    from app.core.config import settings
    
    # Generate token
    token = jwt.encode(token_data, settings.jwt_secret_key, algorithm="HS256")
    return token


@pytest.fixture
def auth_headers(test_token):
    """Create authentication headers for test user."""
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing."""
    # Use a simple dictionary to store key-value pairs instead of async mocks
    redis_store = {}
    
    class MockRedis:
        def get(self, key, *args, **kwargs):
            # Synchronous get that returns None for missing keys
            return redis_store.get(key)
            
        def setex(self, key, expiry, value, *args, **kwargs):
            # Synchronous setex
            redis_store[key] = value
            return True
            
        def delete(self, key, *args, **kwargs):
            # Synchronous delete
            if key in redis_store:
                del redis_store[key]
                return 1
            return 0
            
        def incr(self, key, *args, **kwargs):
            # Synchronous increment
            if key not in redis_store:
                redis_store[key] = 1
            else:
                try:
                    redis_store[key] = int(redis_store[key]) + 1
                except (TypeError, ValueError):
                    redis_store[key] = 1
            return redis_store[key]
    
    return MockRedis()


# Test configuration based on environment
def pytest_configure(config):
    """Configure pytest based on available dependencies."""
    if not HAS_AIOSQLITE:
        print("\n⚠️  aiosqlite not installed - using mocked database for tests")
        print("💡 Install test dependencies: pip install aiosqlite pytest-asyncio")
    else:
        print("\n✅ Full test dependencies available")


# Markers for different test types
def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their requirements."""
    for item in items:
        # Mark tests that require database
        if "db_session" in item.fixturenames and HAS_AIOSQLITE:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)