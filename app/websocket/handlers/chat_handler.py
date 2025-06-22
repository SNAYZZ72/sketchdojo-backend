"""
WebSocket handler for real-time chat functionality
"""
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.application.services.chat_service import ChatService
from app.websocket.connection_manager import get_connection_manager
from app.websocket.handlers.tool_handler import get_tool_handler


logger = logging.getLogger(__name__)


class ChatHandler:
    """Handle real-time chat functionality for webtoon collaboration"""

    def __init__(self, chat_service: Optional[ChatService] = None):
        self.connection_manager = get_connection_manager()
        self.chat_rooms: Dict[str, List[str]] = {}  # room_id -> list of client_ids
        self.client_rooms: Dict[str, str] = {}  # client_id -> room_id
        self.chat_service = chat_service  # Can be None for backward compatibility

    async def handle_join_room(self, client_id: str, message: Dict[str, Any]):
        """Handle client joining a chat room"""
        room_id = message.get("room_id")
        if not room_id:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "room_id is required"}, client_id
            )
            return

        try:
            # Try to parse as UUID to validate format and for database storage
            webtoon_id = UUID(room_id)
        except ValueError:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "Invalid room_id format. Must be a valid UUID."}, client_id
            )
            return

        # Remove client from previous room if any
        await self._leave_current_room(client_id)

        # Add client to new room
        if room_id not in self.chat_rooms:
            self.chat_rooms[room_id] = []

        self.chat_rooms[room_id].append(client_id)
        self.client_rooms[client_id] = room_id

        # Notify client of successful join
        join_message = {
            "type": "chat_room_joined",
            "room_id": room_id,
            "participants": len(self.chat_rooms[room_id]),
        }
        await self.connection_manager.send_personal_message(join_message, client_id)

        # Notify other participants
        await self._broadcast_to_room(
            room_id,
            {
                "type": "participant_joined",
                "room_id": room_id,
                "participants": len(self.chat_rooms[room_id]),
            },
            exclude_client=client_id,
        )
        
        # If chat service is available, send chat history to the client
        if self.chat_service:
            try:
                # Get chat history
                messages = await self.chat_service.get_chat_history(webtoon_id, limit=50)
                
                if messages:
                    # Send chat history
                    history_message = {
                        "type": "chat_history",
                        "room_id": room_id,
                        "messages": [
                            {
                                "type": "chat_message",
                                "room_id": room_id,
                                "client_id": msg.client_id,
                                "text": msg.content,
                                "timestamp": msg.timestamp.isoformat(),
                                "message_id": msg.message_id,
                                "has_tool_calls": len(msg.tool_calls) > 0,
                                "role": msg.role,
                            } for msg in messages
                        ],
                    }
                    await self.connection_manager.send_personal_message(history_message, client_id)
            except Exception as e:
                logger.error(f"Failed to send chat history: {str(e)}")

        logger.info(f"Client {client_id} joined chat room {room_id}")

    async def handle_leave_room(self, client_id: str, message: Dict[str, Any]):
        """Handle client leaving a chat room"""
        await self._leave_current_room(client_id)

    async def handle_chat_message(self, client_id: str, message: Dict[str, Any]):
        """Handle chat message from client"""
        logger.info(f"Received chat message from client {client_id}: {message}")
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            logger.warning(f"Client {client_id} tried to send message without joining a room first")
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "You must join a room first"},
                client_id,
            )
            return

        # Check for message content in either 'text' or 'content' field (for compatibility)
        chat_text = message.get("text", "").strip() or message.get("content", "").strip()
        if not chat_text:
            await self.connection_manager.send_personal_message(
                {"type": "error", "message": "Message text cannot be empty"},
                client_id,
            )
            return

        # Generate a message ID for tracking
        message_id = str(uuid4())
        
        # Check for tool calls in the message
        tool_calls = message.get("tool_calls", [])
        has_tool_calls = len(tool_calls) > 0
        role = message.get("role", "user")
        
        # Create chat message
        chat_message = {
            "type": "chat_message",
            "room_id": room_id,
            "client_id": client_id,
            "text": chat_text,
            "timestamp": datetime.now(UTC).isoformat(),
            "message_id": message_id,
            "has_tool_calls": has_tool_calls,
            "role": role
        }

        # Broadcast to all room participants
        await self._broadcast_to_room(room_id, chat_message)

        logger.debug(
            f"Chat message from {client_id} in room {room_id}: {chat_text[:50]}"
        )
        
        # If chat service available, persist message
        if self.chat_service:
            try:
                # Try to parse room_id as UUID (webtoon_id)
                webtoon_id = UUID(room_id)
                
                # Save message to database
                await self.chat_service.create_message(
                    webtoon_id=webtoon_id,
                    client_id=client_id,
                    role=role,
                    content=chat_text,
                    message_id=message_id,
                    tool_calls=[{
                        "id": tc.get("id", str(uuid.uuid4())),
                        "name": tc.get("name", ""),
                        "arguments": tc.get("arguments", {})
                    } for tc in tool_calls] if tool_calls else None
                )
            except Exception as e:
                logger.error(f"Failed to persist chat message: {str(e)}")
        
        # Process tool calls or generate AI response
        if has_tool_calls:
            logger.info(f"Message from client {client_id} has tool calls, processing")
            await self._process_tool_calls(client_id, room_id, message_id, tool_calls)
        else:
            # For regular user messages, generate an AI response if chat service is available
            if self.chat_service and role == "user":
                logger.info(f"Generating AI response for message from client {client_id} in room {room_id}")
                try:
                    # Send typing indicator first
                    typing_indicator = {
                        "type": "typing_indicator",
                        "room_id": room_id,
                        "client_id": "ai_assistant",
                        "is_typing": True,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    logger.debug(f"Sending typing indicator to room {room_id}")
                    await self._broadcast_to_room(room_id, typing_indicator)
                    
                    # Try to parse room_id as UUID (webtoon_id)
                    webtoon_id = UUID(room_id)
                    
                    # Generate AI response
                    logger.info(f"Calling generate_ai_response for webtoon_id {webtoon_id}")
                    ai_message = await self.chat_service.generate_ai_response(webtoon_id)
                    
                    if ai_message:
                        content_length = len(ai_message.content) if ai_message.content is not None else 0
                        logger.info(f"Received AI response: id={ai_message.id}, content_length={content_length}, has_tool_calls={bool(ai_message.tool_calls)}")
                        # Stop typing indicator
                        typing_indicator["is_typing"] = False
                        await self._broadcast_to_room(room_id, typing_indicator)
                        
                        # Format and broadcast AI response
                        ai_response = {
                            "type": "chat_message",
                            "room_id": room_id,
                            "client_id": "ai_assistant",
                            "text": ai_message.content,
                            "timestamp": ai_message.timestamp.isoformat(),
                            "message_id": ai_message.message_id,
                            "role": "assistant",
                            "has_tool_calls": bool(ai_message.tool_calls)
                        }
                        
                        # Broadcast AI response to all room participants
                        logger.info(f"Broadcasting AI response to room {room_id}")
                        await self._broadcast_to_room(room_id, ai_response)
                        logger.info(f"AI response successfully sent to room {room_id}")
                        
                        # If AI response contains tool calls, process them
                        if ai_message.tool_calls:
                            tool_calls_format = [{
                                "id": tc.id,
                                "name": tc.name,
                                "arguments": tc.arguments
                            } for tc in ai_message.tool_calls]
                            
                            await self._process_tool_calls(
                                "ai_assistant", 
                                room_id, 
                                ai_message.message_id,
                                tool_calls_format
                            )
                except Exception as e:
                    logger.error(f"Error generating AI response: {str(e)}")
                    logger.exception("Full exception details:")
                    # Send error message to client
                    await self.connection_manager.send_personal_message(
                        {
                            "type": "error", 
                            "message": "Failed to generate AI response. Please try again."
                        },
                        client_id
                    )

    async def handle_typing_indicator(self, client_id: str, message: Dict[str, Any]):
        """Handle typing indicator"""
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            return

        is_typing = message.get("is_typing", False)

        typing_message = {
            "type": "typing_indicator",
            "room_id": room_id,
            "client_id": client_id,
            "is_typing": is_typing,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Broadcast to other room participants
        await self._broadcast_to_room(room_id, typing_message, exclude_client=client_id)

    async def handle_client_disconnect(self, client_id: str):
        """Handle client disconnection"""
        await self._leave_current_room(client_id)
        
        # Notify the tool handler about the disconnect
        tool_handler = get_tool_handler()
        await tool_handler.handle_client_disconnect(client_id)

    async def _leave_current_room(self, client_id: str):
        """Remove client from their current room"""
        room_id = self.client_rooms.get(client_id)
        if not room_id:
            return

        # Remove from room
        if room_id in self.chat_rooms and client_id in self.chat_rooms[room_id]:
            self.chat_rooms[room_id].remove(client_id)

            # Clean up empty rooms
            if not self.chat_rooms[room_id]:
                del self.chat_rooms[room_id]
            else:
                # Notify remaining participants
                await self._broadcast_to_room(
                    room_id,
                    {
                        "type": "participant_left",
                        "room_id": room_id,
                        "participants": len(self.chat_rooms[room_id]),
                    },
                )

        # Remove client room mapping
        if client_id in self.client_rooms:
            del self.client_rooms[client_id]

        logger.info(f"Client {client_id} left chat room {room_id}")

    async def _broadcast_to_room(
        self, room_id: str, message: Dict[str, Any], exclude_client: str = None
    ):
        """Broadcast message to all clients in a room"""
        if room_id not in self.chat_rooms:
            return

        for client_id in self.chat_rooms[room_id]:
            if exclude_client and client_id == exclude_client:
                continue

            await self.connection_manager.send_personal_message(message, client_id)

    def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """Get information about a chat room"""
        if room_id not in self.chat_rooms:
            return {"exists": False}

        return {
            "exists": True,
            "room_id": room_id,
            "participant_count": len(self.chat_rooms[room_id]),
            "participants": self.chat_rooms[room_id],
        }

    def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """Get information about a client"""
        room_id = self.client_rooms.get(client_id)
        return {
            "client_id": client_id,
            "current_room": room_id,
            "in_room": room_id is not None,
        }
        
    async def handle_tool_discovery(self, client_id: str, message: Dict[str, Any] = None):
        """Handle tool discovery request"""
        tool_handler = get_tool_handler()
        await tool_handler.handle_tool_discovery(client_id)
    
    async def _process_tool_calls(
        self, client_id: str, room_id: str, message_id: str, tool_calls: List[Dict[str, Any]]
    ):
        """Process tool calls within a message"""
        tool_handler = get_tool_handler()
        
        for i, tool_call in enumerate(tool_calls):
            tool_id = tool_call.get("name")
            parameters = tool_call.get("arguments", {})
            
            if not tool_id:
                await self._send_tool_call_error(
                    client_id, 
                    room_id,
                    message_id,
                    i,
                    "missing_tool_id", 
                    "Tool ID is required"
                )
                continue
            
            # Generate a unique call ID for this specific tool call
            call_id = str(uuid4())
            
            # Forward the tool call to the tool handler
            await tool_handler.handle_tool_call(client_id, {
                "tool_id": tool_id,
                "call_id": call_id,
                "message_id": message_id,
                "parameters": parameters
            })
    
    async def _send_tool_call_error(
        self, 
        client_id: str, 
        room_id: str,
        message_id: str,
        call_index: int,
        error_code: str, 
        error_message: str
    ):
        """Send tool call error to client"""
        tool_error = {
            "type": "tool_call_error",
            "message_id": message_id,
            "call_index": call_index,
            "error_code": error_code,
            "error_message": error_message,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        
        await self.connection_manager.send_personal_message(tool_error, client_id)
        
        logger.error(f"Tool call error for client {client_id}: {error_code} - {error_message}")


# Global chat handler instance
_chat_handler = None


async def get_chat_handler(chat_service: Optional[ChatService] = None) -> ChatHandler:
    """Get the global chat handler instance"""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler(chat_service)
    elif chat_service and not _chat_handler.chat_service:
        # Upgrade existing handler with chat service if needed
        _chat_handler.chat_service = chat_service
    return _chat_handler
