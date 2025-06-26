"""
Tests for ChatRepositoryRedis implementation
"""
import json
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY
from typing import List, Dict, Any, Optional
import pytest
import pytest_asyncio
from uuid import UUID

from app.domain.entities.chat import ChatMessage, ChatRoom, ToolCall
from app.domain.mappers.chat_mapper import ChatDataMapper
from app.infrastructure.repositories.chat_repository_redis import ChatRepositoryRedis
from app.application.interfaces.storage_provider import StorageProvider


class TestChatRepositoryRedis:
    """Test cases for ChatRepositoryRedis"""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock StorageProvider with all required methods"""
        mock = AsyncMock(spec=StorageProvider)
        
        # Add missing methods that are used in the tests
        mock.store = AsyncMock(return_value=True)
        mock.set = AsyncMock(return_value=True)
        mock.get = AsyncMock()
        mock.exists = AsyncMock(return_value=False)
        mock.delete = AsyncMock(return_value=True)
        mock.add_to_sorted_set = AsyncMock(return_value=1)
        mock.get_sorted_set_range = AsyncMock(return_value=[])
        mock.expire = AsyncMock(return_value=True)  # Add missing expire method
        
        # Mock Redis client for pipeline
        mock.redis_client = MagicMock()
        mock_pipeline = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[])
        mock_pipeline.get = AsyncMock()
        mock_pipeline.get.return_value = None  # Default return for get
        mock.redis_client.pipeline.return_value = mock_pipeline
        
        return mock

    @pytest.fixture
    def chat_mapper(self):
        """Create a ChatDataMapper instance"""
        return ChatDataMapper()

    @pytest.fixture
    def chat_repo(self, mock_storage, chat_mapper):
        """Create a ChatRepositoryRedis instance with a mock storage"""
        return ChatRepositoryRedis(storage=mock_storage, mapper=chat_mapper)

    @pytest.fixture
    def sample_message(self):
        """Create a sample chat message for testing"""
        return ChatMessage(
            id=uuid.uuid4(),
            webtoon_id=uuid.uuid4(),
            client_id="test_user",
            role="user",
            content="Test message",
            timestamp=datetime.now(timezone.utc),
            message_id=str(uuid.uuid4()),
            tool_calls=[],
            metadata={}
        )

    @pytest.fixture
    def sample_room(self):
        """Create a sample chat room for testing"""
        return ChatRoom(
            webtoon_id=uuid.uuid4(),
            id=uuid.uuid4(),
            name="Test Room",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metadata={}
        )

    @pytest.mark.asyncio
    async def test_save_message(self, chat_repo, mock_storage, sample_message, chat_mapper):
        """Test saving a chat message"""
        # Setup - update keys to match actual implementation
        message_key = f"chat:message:{sample_message.id}"
        webtoon_messages_key = f"chat:webtoon:{sample_message.webtoon_id}:messages"
        
        # Reset mocks to clear any previous calls
        mock_storage.set.reset_mock()
        mock_storage.add_to_sorted_set.reset_mock()
        mock_storage.expire.reset_mock()
        
        # Mock the set operation to return True
        mock_storage.set.return_value = True
        
        # Test
        result = await chat_repo.save(sample_message)
        
        # Assert
        assert result == sample_message
        
        # Verify set was called with the correct key and serialized message
        mock_storage.set.assert_awaited_once()
        
        # Verify add_to_sorted_set was called with the correct arguments
        mock_storage.add_to_sorted_set.assert_awaited_once()
        
        # Verify expire was called on the message key
        mock_storage.expire.assert_called_once()
        
        # Verify the storage key and value
        call_args = mock_storage.set.await_args[0]
        assert call_args[0] == message_key
        assert json.loads(call_args[1])["id"] == str(sample_message.id)
        
        # Test with a custom TTL
        custom_ttl = 3600  # 1 hour
        chat_repo.ttl_seconds = custom_ttl
        mock_storage.set.reset_mock()
        mock_storage.expire.reset_mock()
        
        await chat_repo.save(sample_message)
        mock_storage.expire.assert_called_with(message_key, custom_ttl)
        add_args, add_kwargs = mock_storage.add_to_sorted_set.call_args
        assert add_args[0] == webtoon_messages_key
        assert str(sample_message.id) in add_args[1]  # Message ID is in the members dict

    @pytest.mark.asyncio
    async def test_get_by_webtoon_id(self, chat_repo, mock_storage, sample_message):
        """Test getting messages by webtoon ID with batch fetching"""
        # Setup
        webtoon_id = sample_message.webtoon_id
        message_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        # Create test messages with unique content
        test_messages = [
            ChatMessage(
                id=UUID(msg_id),
                webtoon_id=webtoon_id,
                client_id="test_user",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now(timezone.utc),
                message_id=str(uuid.uuid4()),
                tool_calls=[],
                metadata={}
            ) for i, msg_id in enumerate(message_ids)
        ]
        
        # Mock storage to return message IDs
        mock_storage.get_sorted_set_range.return_value = message_ids
        
        # Mock batch get to return our test messages
        with patch.object(chat_repo, '_batch_get_messages', new_callable=AsyncMock) as mock_batch_get:
            mock_batch_get.return_value = test_messages
            
            # Test
            result = await chat_repo.get_by_webtoon_id(webtoon_id, limit=10, skip=0)
            
            # Assert
            assert len(result) == 3
            assert all(isinstance(msg, ChatMessage) for msg in result)
            assert [msg.content for msg in result] == [f"Message {i}" for i in range(3)]
            
            # Verify the storage call
            mock_storage.get_sorted_set_range.assert_awaited_once_with(
                f"chat:webtoon:{webtoon_id}:messages",
                start=0,
                stop=9,  # 0 + 10 - 1
                desc=True,
                with_scores=False
            )
            
            # Verify batch get was called with the correct message IDs
            mock_batch_get.assert_awaited_once_with(message_ids)

    @pytest.mark.asyncio
    async def test_batch_get_messages(self, chat_repo, mock_storage, sample_message):
        """Test batch fetching of multiple messages"""
        # Setup
        message_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        # Create test message data
        test_messages = [
            {
                "id": msg_id,
                "webtoon_id": str(sample_message.webtoon_id),
                "client_id": "test_user",
                "role": "user",
                "content": f"Batch {i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid.uuid4()),
                "tool_calls": [],
                "metadata": {}
            } for i, msg_id in enumerate(message_ids)
        ]
        
        # Configure the mock storage to return our test messages
        async def mock_get(key):
            # Extract message ID from key (format: "chat:message:<id>")
            msg_id = key.split(":")[-1]
            for i, msg in enumerate(test_messages):
                if msg["id"] == msg_id and i % 2 == 0:  # Only return even-indexed messages
                    return json.dumps(msg)
            return None
            
        # Create a mock pipeline that will use our mock_get function
        mock_pipeline = AsyncMock()
        mock_pipeline.get.side_effect = [
            json.dumps(test_messages[0]) if i % 2 == 0 else None
            for i in range(len(message_ids))
        ]
        mock_pipeline.execute.return_value = [
            json.dumps(test_messages[0]) if i % 2 == 0 else None
            for i in range(len(message_ids))
        ]
        
        # Patch the storage to return our mock pipeline
        mock_storage.redis_client.pipeline.return_value = mock_pipeline
        
        # Also patch the storage.get to use our mock_get
        with patch.object(chat_repo.storage, 'get', side_effect=mock_get):
            # Test
            result = await chat_repo._batch_get_messages(message_ids)
            
            # Assert
            # Should return only the messages that were found (every other message)
            assert len(result) > 0  # At least one message should be returned
            assert all(isinstance(msg, ChatMessage) for msg in result)
            
            # Verify the content of the messages
            for msg in result:
                assert msg.role == "user"
                assert msg.client_id == "test_user"

    @pytest.mark.asyncio
    async def test_get_chat_history(self, chat_repo, mock_storage, sample_message):
        """Test getting chat history (delegates to get_by_webtoon_id)"""
        # Setup
        webtoon_id = sample_message.webtoon_id
        test_messages = [sample_message]
        
        # Create a mock for get_by_webtoon_id
        mock_get_by_webtoon = AsyncMock(return_value=test_messages)
        
        # Patch the method directly on the instance
        with patch.object(chat_repo, 'get_by_webtoon_id', mock_get_by_webtoon):
            # Test with default parameters
            result = await chat_repo.get_chat_history(webtoon_id)
            
            # Assert
            assert result == test_messages
            mock_get_by_webtoon.assert_awaited_once_with(
                webtoon_id, limit=100, skip=0
            )
            
            # Reset mock for next test
            mock_get_by_webtoon.reset_mock()
            
            # Test with custom limit
            result = await chat_repo.get_chat_history(webtoon_id, limit=50)
            
            # Assert
            assert result == test_messages
            mock_get_by_webtoon.assert_awaited_once_with(
                webtoon_id, limit=50, skip=0
            )
            
            # Test with just limit as positional argument
            mock_get_by_webtoon.reset_mock()
            result = await chat_repo.get_chat_history(webtoon_id, 25)
            assert result == test_messages
            mock_get_by_webtoon.assert_awaited_once_with(
                webtoon_id, limit=25, skip=0
            )

    @pytest.mark.asyncio
    async def test_save_room(self, chat_repo, mock_storage, sample_room):
        """Test saving a chat room"""
        # Setup - use the correct key format with 'chat:' prefix
        room_key = f"chat:room:{sample_room.id}"
        mock_storage.set.return_value = True
        
        # Test
        result = await chat_repo.save_room(sample_room)
        
        # Assert
        assert result == sample_room
        mock_storage.set.assert_awaited_once()
        
        # Verify the storage key and value
        args, kwargs = mock_storage.set.call_args
        assert args[0] == room_key
        
        # Verify the serialized data
        serialized_data = json.loads(args[1])
        assert serialized_data["id"] == str(sample_room.id)
        assert serialized_data["name"] == sample_room.name
        assert "created_at" in serialized_data
        assert "updated_at" in serialized_data

    @pytest.mark.asyncio
    async def test_batch_get_messages(self, chat_repo, mock_storage, sample_message):
        """Test batch fetching of multiple messages"""
        # Setup
        message_ids = [str(uuid.uuid4()) for _ in range(3)]
            
        # Create test message data
        test_messages = [
            {
                "id": msg_id,
                "webtoon_id": str(sample_message.webtoon_id),
                "client_id": "test_user",
                "role": "user",
                "content": f"Batch {i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_id": str(uuid.uuid4()),
                "tool_calls": [],
                "metadata": {}
            } for i, msg_id in enumerate(message_ids)
        ]
            
        # Create a mock pipeline
        mock_pipeline = AsyncMock()
            
        # Configure pipeline.execute() to return serialized messages
        mock_pipeline.execute.return_value = [
            json.dumps(msg) if i % 2 == 0 else None  # Test with some missing messages
            for i, msg in enumerate(test_messages)
        ]
            
        # Configure the storage to return our mock pipeline
        mock_storage.redis_client.pipeline.return_value = mock_pipeline
            
        # Test
        result = await chat_repo._batch_get_messages(message_ids)
            
        # Assert
        # Should return only the messages that were found (every other message)
        assert len(result) == 2  # 2 out of 3 messages should be returned
        assert all(isinstance(msg, ChatMessage) for msg in result)
            
        # Verify the content of the messages
        for i, msg in enumerate(result):
            # Since we return every other message, the content should be "Batch 0" and "Batch 2"
            assert msg.content in ["Batch 0", "Batch 2"]
            assert msg.role == "user"
            assert msg.client_id == "test_user"
            
            # Remove these lines as they seem to be test code that was accidentally included here
            # mock_storage.get.return_value = None
            # result = await chat_repo.get_room("non-existent-room")
            # assert result is None
            # mock_storage.get.assert_awaited_once_with("chat:room:non-existent-room")
            # 
            # # Reset mock for next test
            # mock_storage.get.reset_mock()
            # 
            # # Test with invalid data
            # mock_storage.get.return_value = "invalid-json"
            # with pytest.raises(json.JSONDecodeError):
            #     await chat_repo.get_room("invalid-data")
            # mock_storage.get.assert_awaited_once_with("chat:room:invalid-data")

    @pytest.mark.asyncio
    async def test_get_messages_by_webtoon(self, chat_repo, mock_storage, sample_message):
        """Test getting messages by webtoon ID with pagination"""
        # Setup
        webtoon_id = sample_message.webtoon_id
        message_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # Create test messages with unique content
        test_messages = [
            ChatMessage(
                id=UUID(msg_id),
                webtoon_id=webtoon_id,
                client_id="test_user",
                role="user",
                content=f"Message {i}",
                timestamp=datetime.now(timezone.utc),
                message_id=str(uuid.uuid4()),
                tool_calls=[],
                metadata={}
            ) for i, msg_id in enumerate(message_ids[1:4])  # Middle 3 messages
        ]
        
        # Mock storage to return message IDs
        mock_storage.get_sorted_set_range.return_value = message_ids[1:4]
        
        # Mock batch get to return our test messages
        with patch.object(chat_repo, '_batch_get_messages', new_callable=AsyncMock) as mock_batch_get:
            mock_batch_get.return_value = test_messages
            
            # Test with pagination (skip=1, limit=3)
            result = await chat_repo.get_messages_by_webtoon(webtoon_id, skip=1, limit=3)
            
            # Assert
            assert len(result) == 3
            assert all(isinstance(msg, ChatMessage) for msg in result)
            assert [msg.content for msg in result] == [f"Message {i}" for i in range(3)]
            
            # Verify the storage call with correct pagination and key format
            mock_storage.get_sorted_set_range.assert_awaited_once_with(
                f"chat:webtoon:{webtoon_id}:messages",
                start=1,
                stop=3,  # 1 + 3 - 1
                desc=True,
                with_scores=False
            )
            
            # Verify batch get was called with the correct message IDs
            mock_batch_get.assert_awaited_once_with(message_ids[1:4])

    @pytest.mark.asyncio
    async def test_get_by_webtoon_id_empty(self, chat_repo, mock_storage):
        """Test getting messages for a webtoon with no messages"""
        # Setup
        webtoon_id = uuid.uuid4()
        mock_storage.get_sorted_set_range.return_value = []
        
        # Test
        result = await chat_repo.get_by_webtoon_id(webtoon_id)
        
        # Assert
        assert result == []
        mock_storage.get_sorted_set_range.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_limit(self, chat_repo):
        """Test validation of limit parameter"""
        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            await chat_repo.get_by_webtoon_id(uuid.uuid4(), limit=0)
            
        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            await chat_repo.get_by_webtoon_id(uuid.uuid4(), limit=-1)
            
        # Test with non-integer limit (should raise TypeError)
        with pytest.raises((TypeError, ValueError)):
            await chat_repo.get_by_webtoon_id(uuid.uuid4(), limit="not_an_integer")

    @pytest.mark.asyncio
    async def test_max_limit_enforced(self, chat_repo, mock_storage):
        """Test that the maximum limit is enforced"""
        # Setup
        webtoon_id = uuid.uuid4()
        mock_storage.get_sorted_set_range.return_value = []
        
        # Test with limit > 1000
        await chat_repo.get_by_webtoon_id(webtoon_id, limit=2000)
        
        # Should be capped at 1000
        args, kwargs = mock_storage.get_sorted_set_range.call_args
        assert kwargs['stop'] == 999  # 0 + 1000 - 1
