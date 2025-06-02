# tests/conftest.py
"""
Pytest configuration and fixtures
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.application.services.generation_service import GenerationService
from app.application.services.webtoon_service import WebtoonService
from app.config import Settings
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.infrastructure.storage.memory_storage import MemoryStorage


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings configuration"""
    return Settings(
        environment="test",
        debug=True,
        redis_url="redis://localhost:6379/15",
        celery_broker_url="redis://localhost:6379/15",
        celery_result_backend="redis://localhost:6379/15",
        openai_api_key="test-key",
        secret_key="test-secret",
        log_level="DEBUG",
    )


@pytest.fixture
async def memory_storage():
    """In-memory storage for testing"""
    storage = MemoryStorage()
    yield storage
    storage.clear_all()


@pytest.fixture
async def webtoon_repository(memory_storage):
    """Webtoon repository with memory storage"""
    return WebtoonRepository(memory_storage)


@pytest.fixture
async def task_repository(memory_storage):
    """Task repository with memory storage"""
    return TaskRepository(memory_storage)


@pytest.fixture
async def webtoon_service(webtoon_repository):
    """Webtoon service for testing"""
    return WebtoonService(webtoon_repository)


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for testing"""
    ai_provider = AsyncMock()

    # Mock story generation
    ai_provider.generate_story.return_value = {
        "title": "Test Story",
        "plot_summary": "A test story for unit testing",
        "setting": {"location": "Test City", "time_period": "Modern"},
        "main_characters": [
            {
                "name": "Test Hero",
                "description": "Brave protagonist",
                "role": "protagonist",
            }
        ],
        "theme": "Adventure",
        "mood": "Exciting",
        "key_scenes": ["Opening scene", "Conflict", "Resolution"],
    }

    # Mock scene generation
    ai_provider.generate_scene_descriptions.return_value = [
        {
            "visual_description": "Hero standing in the city",
            "characters": ["Test Hero"],
            "dialogue": [{"character": "Test Hero", "text": "Let's begin!"}],
            "setting": "City street",
            "mood": "determined",
            "panel_size": "full",
            "camera_angle": "medium",
            "special_effects": [],
        }
    ]

    # Mock dialogue generation
    ai_provider.generate_dialogue.return_value = [
        {"character": "Test Hero", "text": "Hello, world!"}
    ]

    # Mock visual enhancement
    ai_provider.enhance_visual_description.return_value = "Enhanced visual description"

    return ai_provider


@pytest.fixture
def mock_image_generator():
    """Mock image generator for testing"""
    image_gen = AsyncMock()
    image_gen.is_available.return_value = True
    image_gen.generate_image.return_value = (
        "/path/to/test/image.png",
        "http://localhost:8000/static/test_image.png",
    )
    image_gen.enhance_prompt.return_value = "Enhanced prompt"
    return image_gen


@pytest.fixture
async def generation_service(
    mock_ai_provider, mock_image_generator, webtoon_repository, task_repository
):
    """Generation service with mocked dependencies"""
    return GenerationService(
        ai_provider=mock_ai_provider,
        image_generator=mock_image_generator,
        webtoon_repository=webtoon_repository,
        task_repository=task_repository,
    )


@pytest.fixture
def sample_webtoon_data():
    """Sample webtoon data for testing"""
    return {
        "title": "Test Webtoon",
        "description": "A test webtoon for unit testing",
        "art_style": "webtoon",
    }


@pytest.fixture
def sample_generation_request():
    """Sample generation request data"""
    from app.application.dto.generation_dto import GenerationRequestDTO
    from app.domain.value_objects.style import ArtStyle

    return GenerationRequestDTO(
        prompt="Create a story about a brave hero in a magical world",
        art_style=ArtStyle.WEBTOON,
        num_panels=4,
        character_descriptions=["Brave hero with sword"],
        additional_context="Should be family-friendly",
    )
