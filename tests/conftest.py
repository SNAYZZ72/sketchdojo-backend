# =============================================================================
# tests/conftest.py
# =============================================================================
import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import TestSettings
from app.core.database import Base, get_db
from app.domain.models.user import User, UserRole, UserStatus
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL, poolclass=StaticPool, connect_args={"check_same_thread": False}
)

# Create test session factory
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    """Create a test client."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
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


@pytest.fixture
async def admin_user(db_session):
    """Create an admin test user."""
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


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    # In a real test, you would generate actual JWT tokens
    return {"Authorization": "Bearer test_token"}
