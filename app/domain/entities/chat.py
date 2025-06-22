# app/domain/entities/chat.py
"""
Chat domain entities
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class ToolCall:
    """
    Represents a tool call within a chat message
    """
    id: str
    name: str
    arguments: Dict = field(default_factory=dict)
    status: str = "pending"  # pending, executing, succeeded, failed
    result: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class ChatMessage:
    """
    Represents a chat message in a webtoon project
    """
    webtoon_id: UUID  # Link to the webtoon/project
    client_id: str  # The client ID that sent the message
    role: str  # user, assistant, system
    content: str  # The message content
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    message_id: str = field(default_factory=lambda: str(uuid4()))  # External message ID for WebSocket tracking
    tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)  # For any additional data


@dataclass
class ChatRoom:
    """
    Represents a chat room, typically linked to a webtoon project
    """
    webtoon_id: UUID  # Link to the webtoon/project
    id: UUID = field(default_factory=uuid4)
    name: str = "Chat"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict = field(default_factory=dict)  # For any additional data
