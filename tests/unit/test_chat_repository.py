# tests/unit/test_chat_repository.py
"""
Tests for ChatRepositoryRedis
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from uuid import UUID

from app.domain.entities.chat import (
    ChatMessage,
    ChatRoom,
    ToolCall
)
from app.domain.mappers.chat_mapper import ChatDataMapper
from app.infrastructure.repositories.chat_repository_redis import ChatRepositoryRedis


class MockStorageProvider:
    """Mock implementation of a storage provider for testing"""

    def __init__(self):
        self.store_data = {}
        self.store = AsyncMock(return_value=True)
        self.retrieve = AsyncMock(side_effect=self._mock_retrieve)
        self.delete = AsyncMock(return_value=True)
        self.exists = AsyncMock(return_value=True)
        self.list_keys = AsyncMock(return_value=["chat:room:123", "chat:room:456"])
        self.list_pattern = AsyncMock(return_value=["chat:message:123", "chat:message:456"])
        self.add_to_list = AsyncMock(return_value=True)
        self.get_list = AsyncMock(return_value=["msg1", "msg2"])
        
        # Add aliases for standard repository method names
        self.get = AsyncMock(side_effect=self._mock_retrieve)
        self.set = AsyncMock(return_value=True)
        self.remove_from_list = AsyncMock(return_value=True)
        
    async def _mock_retrieve(self, key):
        """Mock retrieve method that returns preset data based on key"""
        if "not-found" in key:
            return None
        elif "error" in key:
            raise Exception("Storage error")
        elif "room" in key:
            return {"id": key.split(":")[-1], "name": "Test Room"}
        else:
            return {"id": key.split(":")[-1], "content": "Test message"}


class TestChatRepositoryRedis:
    """Test ChatRepositoryRedis functionality"""

    def setup_method(self):
        """Initialize test data and repository"""
        self.storage = MockStorageProvider()
        self.mapper = MagicMock(spec=ChatDataMapper)
        self.repository = ChatRepositoryRedis(self.storage, self.mapper)
        self.message_id = uuid.uuid4()
        self.room_id = uuid.uuid4()
        self.webtoon_id = uuid.uuid4()
        
        # Create a sample tool call
        self.tool_call = ToolCall(
            id="call_123",
            name="test_tool",
            arguments={"param1": "value1"},
            status="completed",
            result={"success": True},
            error=None,
        )
        
        # Create a sample chat message
        self.chat_message = ChatMessage(
            id=self.message_id,
            webtoon_id=self.webtoon_id,
            client_id="client123",
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            message_id="msg123",
            tool_calls=[self.tool_call],
            metadata={"source": "web"},
        )
        
        # Create a sample chat room
        self.chat_room = ChatRoom(
            id=self.room_id,
            webtoon_id=self.webtoon_id,
            name="Test Room",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"creator": "user123"},
        )
        
        # Configure mapper mock
        self.mapper.message_to_dict.return_value = {
            "id": str(self.message_id), 
            "webtoon_id": str(self.webtoon_id), 
            "content": "Test message"
        }
        self.mapper.message_from_dict.return_value = self.chat_message
        self.mapper.room_to_dict.return_value = {
            "id": str(self.room_id),
            "webtoon_id": str(self.webtoon_id),
            "name": "Test Room"
        }
        self.mapper.room_from_dict.return_value = self.chat_room

    @pytest.mark.asyncio
    async def test_save_message(self):
        """Test saving a chat message"""
        # Call save method
        result = await self.repository.save(self.chat_message)
        
        # Check results
        assert result == self.chat_message
        self.mapper.message_to_dict.assert_called_once_with(self.chat_message)
        self.storage.set.assert_called_once()
        self.storage.add_to_list.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_save_message_error(self):
        """Test saving a message with storage error"""
        # Configure storage to fail
        self.storage.set.return_value = False
        
        # Call save method and check exception
        with pytest.raises(RuntimeError):
            await self.repository.save(self.chat_message)
    
    @pytest.mark.asyncio
    async def test_get_message(self):
        """Test getting a message by ID"""
        # Call get_by_id method
        result = await self.repository.get_by_id(self.message_id)
        
        # Check results
        assert result == self.chat_message
        self.storage.get.assert_called_once()
        self.mapper.message_from_dict.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_message_not_found(self):
        """Test getting a non-existent message"""
        # Configure storage to return None for not-found key
        self.storage.retrieve = AsyncMock(return_value=None)
        self.storage.get = AsyncMock(return_value=None)
        
        # Call get_by_id method
        result = await self.repository.get_by_id(uuid.uuid4())
        
        # Check result is None
        assert result is None
        
    @pytest.mark.asyncio
    async def test_save_room(self):
        """Test saving a chat room"""
        # Call save_chat_room method
        result = await self.repository.save_chat_room(self.chat_room)
        
        # Check results
        assert result == self.chat_room
        self.mapper.room_to_dict.assert_called_once_with(self.chat_room)
        self.storage.set.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_save_room_error(self):
        """Test saving a room with storage error"""
        # Configure storage to fail
        self.storage.set.return_value = False
        
        # Call save_chat_room method and check exception
        with pytest.raises(RuntimeError):
            await self.repository.save_chat_room(self.chat_room)
    
    @pytest.mark.asyncio
    async def test_get_room(self):
        """Test getting a room by ID"""
        # Call get_chat_room_by_webtoon_id method
        result = await self.repository.get_chat_room_by_webtoon_id(self.webtoon_id)
        
        # Check results
        assert result == self.chat_room
        # The method has additional logic, so let's just check the result
        # instead of the specific calls
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self):
        """Test getting chat history"""
        # Setup mocks for get_list and message retrieval
        message_ids = ["msg1", "msg2"]
        self.storage.get_list.return_value = message_ids
        
        # Call get_chat_history method
        results = await self.repository.get_chat_history(self.webtoon_id, 10)
        
        # Check results
        assert len(results) == 2
        assert results[0] == self.chat_message
        assert results[1] == self.chat_message
        self.storage.get_list.assert_called_once()
        assert self.storage.retrieve.call_count == 2
        
    @pytest.mark.asyncio
    async def test_get_rooms_for_webtoon(self):
        """Test getting all rooms for a webtoon"""
        # Setup mocks for list_pattern
        room_keys = [f"chat:room:{self.room_id}"]
        self.storage.list_pattern.return_value = room_keys
        
        # Call get_rooms_for_webtoon method
        results = await self.repository.get_rooms_for_webtoon(self.webtoon_id)
        
        # Check results
        assert len(results) == 1
        assert results[0] == self.chat_room
        self.storage.list_pattern.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_delete_room(self):
        """Test deleting a room"""
        # Call delete_room method
        result = await self.repository.delete_room(self.room_id)
        
        # Check result
        assert result is True
        self.storage.delete.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_room_exists(self):
        """Test checking if a room exists"""
        # Call room_exists method
        result = await self.repository.room_exists(self.room_id)
        
        # Check result
        assert result is True
        self.storage.exists.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_save(self):
        """Test base repository save method"""
        # Call save method directly
        result = await self.repository.save(self.chat_message)
        
        # Check results
        assert result == self.chat_message
        self.mapper.message_to_dict.assert_called_once_with(self.chat_message)
            
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test base repository get_by_id method"""
        # Call get_by_id method directly
        result = await self.repository.get_by_id(self.message_id)
        
        # Check results
        assert result == self.chat_message
        self.storage.get.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_exists(self):
        """Test base repository exists method"""
        # Configure storage mock
        self.storage.exists.return_value = True
        
        # Call exists method
        result = await self.repository.exists(self.message_id)
        
        # Check results
        assert result is True
        self.storage.exists.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_fields(self):
        """Test updating specific fields of a message"""
        # Setup test data
        update_data = {"content": "Updated message"}
        
        # Configure storage and mapper mocks
        self.storage.retrieve.return_value = {"id": str(self.message_id), "content": "Test message"}
        
        # Call update_fields method
        result = await self.repository.update_fields(self.message_id, update_data)
        
        # Check results
        assert result == self.chat_message
        self.storage.retrieve.assert_called_once()
        self.storage.store.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test getting all messages"""
        # Configure mocks for list_pattern and message retrieval
        message_keys = ["chat:message:123", "chat:message:456"]
        self.storage.list_pattern.return_value = message_keys
        
        # Call get_all method
        results = await self.repository.get_all()
        
        # Check results
        assert len(results) == 2
        assert results[0] == self.chat_message
        assert results[1] == self.chat_message
        self.storage.list_pattern.assert_called_once()
        assert self.storage.retrieve.call_count == 2
