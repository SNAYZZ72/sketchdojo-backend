# app/api/v1/routes/chat.py
"""
API routes for chat functionality
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.schemas.chat import ChatMessageResponse
from app.application.services.chat_service import ChatService
from app.dependencies import get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get(
    "/webtoons/{webtoon_id}",
    response_model=List[ChatMessageResponse],
    summary="Get chat history for a webtoon",
    description="Retrieves the chat message history for a specific webtoon project.",
)
async def get_webtoon_chat_history(
    webtoon_id: UUID,
    limit: int = Query(50, description="Maximum number of messages to return", ge=1, le=100),
    skip: int = Query(0, description="Number of messages to skip for pagination", ge=0),
    chat_service: ChatService = Depends(get_chat_service),
) -> List[ChatMessageResponse]:
    """
    Get chat history for a webtoon
    
    Args:
        webtoon_id: Webtoon UUID
        limit: Maximum number of messages to return (1-100)
        skip: Number of messages to skip for pagination
        chat_service: Chat service dependency
        
    Returns:
        List of chat messages
    """
    messages = await chat_service.get_chat_history(
        webtoon_id=webtoon_id, limit=limit, skip=skip
    )
    
    # Convert domain entities to API response models
    return [
        ChatMessageResponse(
            id=str(message.id),
            webtoon_id=str(message.webtoon_id),
            client_id=message.client_id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            message_id=message.message_id,
            tool_calls=[
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                    "status": tc.status,
                    "result": tc.result,
                    "error": tc.error,
                }
                for tc in message.tool_calls
            ],
            metadata=message.metadata,
        )
        for message in messages
    ]
