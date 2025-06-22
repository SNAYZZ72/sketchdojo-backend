# tests/unit/test_chat_mapper.py
"""
Tests for ChatDataMapper
"""
import uuid
from datetime import datetime

import pytest
from uuid import UUID

from app.domain.entities.chat import ChatMessage, ChatRoom, ToolCall
from app.domain.mappers.chat_mapper import ChatDataMapper


class TestChatDataMapper:
    """Test ChatDataMapper functionality"""

    def setup_method(self):
        """Initialize test data and mapper"""
        self.mapper = ChatDataMapper()
        self.message_id = uuid.uuid4()
        self.webtoon_id = uuid.uuid4()
        self.room_id = uuid.uuid4()
        
        # Create a sample tool call
        self.tool_call = ToolCall(
            id="call_123",
            name="test_tool",
            arguments={"param1": "value1", "param2": "value2"},
            status="completed",
            result={"success": True, "data": "result data"},
            error=None,
        )
        
        # Create a sample chat message
        self.chat_message = ChatMessage(
            id=self.message_id,
            webtoon_id=self.webtoon_id,
            client_id="client123",
            role="user",
            content="Hello, this is a test message",
            timestamp=datetime.now(),
            message_id="msg123",
            tool_calls=[self.tool_call],
            metadata={"source": "web", "session": "session123"},
        )
        
        # Create a sample chat room
        self.chat_room = ChatRoom(
            id=self.room_id,
            webtoon_id=self.webtoon_id,
            name="Test Chat Room",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"creator": "user123", "participants": ["user1", "user2"]},
        )

    def test_message_to_dict(self):
        """Test conversion of ChatMessage to dict"""
        # Convert to dict
        message_dict = self.mapper.message_to_dict(self.chat_message)
        
        # Validate top-level properties
        assert message_dict["id"] == str(self.message_id)
        assert message_dict["webtoon_id"] == str(self.webtoon_id)
        assert message_dict["client_id"] == "client123"
        assert message_dict["role"] == "user"
        assert message_dict["content"] == "Hello, this is a test message"
        assert message_dict["message_id"] == "msg123"
        
        # Validate tool calls
        assert len(message_dict["tool_calls"]) == 1
        tool_call_dict = message_dict["tool_calls"][0]
        assert tool_call_dict["id"] == "call_123"
        assert tool_call_dict["name"] == "test_tool"
        assert tool_call_dict["arguments"] == {"param1": "value1", "param2": "value2"}
        assert tool_call_dict["status"] == "completed"
        assert tool_call_dict["result"] == {"success": True, "data": "result data"}
        
        # Validate metadata
        assert message_dict["metadata"] == {"source": "web", "session": "session123"}

    def test_message_from_dict(self):
        """Test conversion from dict to ChatMessage"""
        # First convert to dict
        message_dict = self.mapper.message_to_dict(self.chat_message)
        
        # Then convert back to object
        message = self.mapper.message_from_dict(message_dict)
        
        # Validate object
        assert isinstance(message, ChatMessage)
        assert message.id == self.message_id
        assert message.webtoon_id == self.webtoon_id
        assert message.client_id == "client123"
        assert message.role == "user"
        assert message.content == "Hello, this is a test message"
        
        # Validate tool calls
        assert len(message.tool_calls) == 1
        tool_call = message.tool_calls[0]
        assert isinstance(tool_call, ToolCall)
        assert tool_call.id == "call_123"
        assert tool_call.name == "test_tool"
        assert tool_call.arguments == {"param1": "value1", "param2": "value2"}
        assert tool_call.status == "completed"
        
        # Validate metadata
        assert message.metadata == {"source": "web", "session": "session123"}

    def test_room_to_dict(self):
        """Test conversion of ChatRoom to dict"""
        # Convert to dict
        room_dict = self.mapper.room_to_dict(self.chat_room)
        
        # Validate properties
        assert room_dict["id"] == str(self.room_id)
        assert room_dict["webtoon_id"] == str(self.webtoon_id)
        assert room_dict["name"] == "Test Chat Room"
        assert "created_at" in room_dict
        assert "updated_at" in room_dict
        
        # Validate metadata
        assert room_dict["metadata"] == {
            "creator": "user123", 
            "participants": ["user1", "user2"]
        }

    def test_room_from_dict(self):
        """Test conversion from dict to ChatRoom"""
        # First convert to dict
        room_dict = self.mapper.room_to_dict(self.chat_room)
        
        # Then convert back to object
        room = self.mapper.room_from_dict(room_dict)
        
        # Validate object
        assert isinstance(room, ChatRoom)
        assert room.id == self.room_id
        assert room.webtoon_id == self.webtoon_id
        assert room.name == "Test Chat Room"
        
        # Validate metadata
        assert room.metadata == {
            "creator": "user123", 
            "participants": ["user1", "user2"]
        }
        
    def test_message_round_trip_conversion(self):
        """Test that converting a message to dict and back preserves all properties"""
        # Convert to dict and back
        message_dict = self.mapper.message_to_dict(self.chat_message)
        message_new = self.mapper.message_from_dict(message_dict)
        
        # Test equality of key properties
        assert message_new.id == self.chat_message.id
        assert message_new.webtoon_id == self.chat_message.webtoon_id
        assert message_new.client_id == self.chat_message.client_id
        assert message_new.role == self.chat_message.role
        assert message_new.content == self.chat_message.content
        
        # Test tool calls
        assert len(message_new.tool_calls) == len(self.chat_message.tool_calls)
        assert message_new.tool_calls[0].id == self.chat_message.tool_calls[0].id
        assert message_new.tool_calls[0].name == self.chat_message.tool_calls[0].name
        
        # Test metadata
        assert message_new.metadata == self.chat_message.metadata
        
    def test_room_round_trip_conversion(self):
        """Test that converting a room to dict and back preserves all properties"""
        # Convert to dict and back
        room_dict = self.mapper.room_to_dict(self.chat_room)
        room_new = self.mapper.room_from_dict(room_dict)
        
        # Test equality of key properties
        assert room_new.id == self.chat_room.id
        assert room_new.webtoon_id == self.chat_room.webtoon_id
        assert room_new.name == self.chat_room.name
        
        # Test metadata
        assert room_new.metadata == self.chat_room.metadata
