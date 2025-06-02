# tests/conftest.py
"""
Pytest configuration and fixtures
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

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


@pytest_asyncio.fixture
async def memory_storage():
    """In-memory storage for testing"""
    storage = MemoryStorage()
    yield storage
    storage.clear_all()


@pytest_asyncio.fixture
async def webtoon_repository(memory_storage):
    """Webtoon repository with memory storage"""
    return WebtoonRepository(memory_storage)


@pytest_asyncio.fixture
async def task_repository(memory_storage):
    """Task repository with memory storage"""
    return TaskRepository(memory_storage)


@pytest_asyncio.fixture
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

    # Create scene descriptions template
    scene_templates = [
        {
            "visual_description": "Hero standing in the city",
            "characters": ["Test Hero"],
            "dialogue": [{"character": "Test Hero", "text": "Let's begin!"}],
            "setting": "City street",
            "mood": "determined",
            "panel_size": "full",
            "camera_angle": "medium",
            "special_effects": [],
        },
        {
            "visual_description": "Hero confronts the villain",
            "characters": ["Test Hero", "Villain"],
            "dialogue": [{"character": "Test Hero", "text": "I will stop you!"}],
            "setting": "Dark alley",
            "mood": "tense",
            "panel_size": "half",
            "camera_angle": "low",
            "special_effects": [],
        },
        {
            "visual_description": "Epic battle scene",
            "characters": ["Test Hero", "Villain"],
            "dialogue": [{"character": "Test Hero", "text": "For justice!"}],
            "setting": "City rooftop",
            "mood": "action",
            "panel_size": "full",
            "camera_angle": "wide",
            "special_effects": ["explosion"],
        },
        {
            "visual_description": "Victory celebration",
            "characters": ["Test Hero", "Citizens"],
            "dialogue": [{"character": "Test Hero", "text": "Peace is restored!"}],
            "setting": "City square",
            "mood": "triumphant",
            "panel_size": "full",
            "camera_angle": "high",
            "special_effects": ["sunset"],
        },
    ]

    # Make generate_scene_descriptions dynamic based on requested panel count
    def mock_generate_scenes(*args, **kwargs):
        # The method is called with positional args: generate_scene_descriptions(story_data, num_panels)
        # If called with positional args
        if len(args) >= 2:
            story_data = args[0]
            num_panels = args[1]
        # If called with keyword args
        else:
            story_data = kwargs.get("story_data", {})
            num_panels = kwargs.get("num_panels", 4)  # Default to 4 if not specified

        # Return only the requested number of panels
        return scene_templates[:num_panels]

    # Set up the mock to use our dynamic function
    ai_provider.generate_scene_descriptions = AsyncMock(
        side_effect=mock_generate_scenes
    )

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
    # Use a regular MagicMock for synchronous methods
    image_gen.is_available = MagicMock(return_value=True)
    # For async methods, use AsyncMock with proper return values
    async_generate_mock = AsyncMock()
    async_generate_mock.return_value = (
        "/path/to/test/image.png",
        "http://localhost:8000/static/test_image.png",
    )
    image_gen.generate_image = async_generate_mock

    async_enhance_mock = AsyncMock()
    async_enhance_mock.return_value = "Enhanced prompt"
    image_gen.enhance_prompt = async_enhance_mock
    return image_gen


@pytest_asyncio.fixture
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
