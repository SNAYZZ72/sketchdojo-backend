# app/domain/repositories/chat_repository.py
"""
Repository interface for chat message persistence
"""
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat import ChatMessage, ChatRoom
from app.domain.repositories.base_repository import BaseRepository


class ChatRepository(BaseRepository[ChatMessage]):
    """Repository interface for chat message persistence"""

    async def get_by_webtoon_id(self, webtoon_id: UUID, limit: int = 100, skip: int = 0) -> List[ChatMessage]:
        """
        Get chat messages for a specific webtoon
        
        Args:
            webtoon_id: The ID of the webtoon
            limit: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)
            
        Returns:
            List of chat messages
        """
        pass
    
    async def get_chat_room_by_webtoon_id(self, webtoon_id: UUID) -> Optional[ChatRoom]:
        """
        Get chat room for a specific webtoon
        
        Args:
            webtoon_id: The ID of the webtoon
            
        Returns:
            Chat room if it exists, None otherwise
        """
        pass
