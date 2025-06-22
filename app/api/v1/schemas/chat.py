# app/api/v1/schemas/chat.py
"""
API schemas for chat functionality
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCallResponse(BaseModel):
    """Tool call within a chat message"""
    
    id: str = Field(..., description="Unique ID of the tool call")
    name: str = Field(..., description="Name of the tool being called")
    arguments: Dict = Field(default_factory=dict, description="Arguments passed to the tool")
    status: str = Field(default="pending", description="Status of the tool call: pending, executing, succeeded, failed")
    result: Optional[Dict] = Field(None, description="Result of the tool call if successful")
    error: Optional[str] = Field(None, description="Error message if the tool call failed")


class ChatMessageResponse(BaseModel):
    """Chat message response model"""
    
    id: str = Field(..., description="Unique ID of the message")
    webtoon_id: str = Field(..., description="ID of the webtoon the message belongs to")
    client_id: str = Field(..., description="ID of the client that sent the message")
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="When the message was sent")
    message_id: str = Field(..., description="External message ID for WebSocket tracking")
    tool_calls: List[ToolCallResponse] = Field(default_factory=list, description="Tool calls in this message")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config"""
        
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ChatRoomResponse(BaseModel):
    """Chat room response model"""
    
    id: str = Field(..., description="Unique ID of the chat room")
    webtoon_id: str = Field(..., description="ID of the webtoon the room belongs to")
    name: str = Field(..., description="Name of the chat room")
    created_at: datetime = Field(..., description="When the room was created")
    updated_at: datetime = Field(..., description="When the room was last updated")
    participant_count: int = Field(0, description="Number of current participants")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config"""
        
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
