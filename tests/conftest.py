# tests/conftest.py
"""
Pytest configuration and fixtures
"""
import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_asyncio import fixture as async_fixture

from app.domain.entities.chat import ChatMessage, ChatRoom, ToolCall
from app.domain.entities.generation_task import GenerationTask, TaskProgress, TaskStatus, TaskType
from app.domain.entities.webtoon import Webtoon
from app.domain.entities.character import Character
from app.domain.entities.panel import Panel
from app.domain.mappers.chat_mapper import ChatDataMapper
from app.domain.mappers.task_mapper import TaskDataMapper
from app.domain.mappers.webtoon_mapper import WebtoonDataMapper


class MockStorageProvider:
    """Mock storage provider for testing repositories"""
    
    def __init__(self):
        self.store_data = {}
        self.store = AsyncMock(return_value=True)
        self.retrieve = AsyncMock(return_value=None)
        self.delete = AsyncMock(return_value=True)
        self.exists = AsyncMock(return_value=True)
        self.list_keys = AsyncMock(return_value=[])
        self.list_pattern = AsyncMock(return_value=[])
        self.add_to_list = AsyncMock(return_value=True)
        self.get_list = AsyncMock(return_value=[])


@pytest.fixture
def mock_storage():
    """Return a mock storage provider"""
    return MockStorageProvider()


@pytest.fixture
def webtoon_mapper():
    """Return a real WebtoonDataMapper instance"""
    return WebtoonDataMapper()


@pytest.fixture
def task_mapper():
    """Return a real TaskDataMapper instance"""
    return TaskDataMapper()


@pytest.fixture
def chat_mapper():
    """Return a real ChatDataMapper instance"""
    return ChatDataMapper()


@pytest.fixture
def mock_webtoon_mapper():
    """Return a mock WebtoonDataMapper"""
    mapper = MagicMock(spec=WebtoonDataMapper)
    return mapper


@pytest.fixture
def mock_task_mapper():
    """Return a mock TaskDataMapper"""
    mapper = MagicMock(spec=TaskDataMapper)
    return mapper


@pytest.fixture
def mock_chat_mapper():
    """Return a mock ChatDataMapper"""
    mapper = MagicMock(spec=ChatDataMapper)
    return mapper


@pytest.fixture
def sample_webtoon():
    """Return a sample Webtoon entity"""
    webtoon_id = uuid.uuid4()
    character_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    
    character = Character(
        id=character_id,
        name="Test Character",
        description="A test character",
        personality=["brave", "smart"],
        backstory="A long time ago...",
        image_url="http://example.com/character.jpg",
    )
    
    panel = Panel(
        id=panel_id,
        sequence_number=1,
        description="Test panel",
        image_url="http://example.com/panel.jpg",
        character_ids=[character_id],
        dialogue=[{"character_id": str(character_id), "text": "Hello world!"}],
    )
    
    return Webtoon(
        id=webtoon_id,
        title="Test Webtoon",
        description="A test webtoon",
        art_style="webtoon",
        panels=[panel],
        characters=[character],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_published=False,
        metadata={"tags": ["test", "sample"]},
    )


@pytest.fixture
def sample_task():
    """Return a sample GenerationTask entity"""
    task_id = uuid.uuid4()
    
    progress = TaskProgress(
        current_step=2,
        total_steps=5,
        current_operation="Processing scene data",
        percentage=40,
    )
    
    return GenerationTask(
        id=task_id,
        task_type=TaskType.GENERATE_STORY,
        status=TaskStatus.IN_PROGRESS,
        progress=progress,
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=None,
        error_message=None,
        result={"partial_data": "Some partial results"},
        input_data={"title": "Test Story", "theme": "adventure"},
        metadata={"user_id": "user123", "priority": "high"},
    )


@pytest.fixture
def sample_chat_message():
    """Return a sample ChatMessage entity"""
    message_id = uuid.uuid4()
    webtoon_id = uuid.uuid4()
    
    tool_call = ToolCall(
        id="call_123",
        name="test_tool",
        arguments={"param1": "value1", "param2": "value2"},
        status="completed",
        result={"success": True, "data": "result data"},
        error=None,
    )
    
    return ChatMessage(
        id=message_id,
        webtoon_id=webtoon_id,
        client_id="client123",
        role="user",
        content="Hello, this is a test message",
        timestamp=datetime.now(),
        message_id="msg123",
        tool_calls=[tool_call],
        metadata={"source": "web", "session": "session123"},
    )


@pytest.fixture
def sample_chat_room():
    """Return a sample ChatRoom entity"""
    room_id = uuid.uuid4()
    webtoon_id = uuid.uuid4()
    
    return ChatRoom(
        id=room_id,
        webtoon_id=webtoon_id,
        name="Test Chat Room",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={"creator": "user123", "participants": ["user1", "user2"]},
    )


# Configure pytest to handle asyncio
@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
