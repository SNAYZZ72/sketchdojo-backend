"""
WebSocket handler for real-time chat functionality
"""
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, cast
from uuid import UUID, uuid4

from fastapi import WebSocket

from app.application.services.chat_service import ChatService
from app.websocket.connection_manager import ConnectionManager, get_connection_manager
from app.websocket.room_manager import get_room_manager
from app.websocket.handlers.base_handler import BaseWebSocketHandler, message_handler
from app.websocket.handlers.tool_handler import get_tool_handler
from app.websocket.exceptions import WebSocketValidationError


logger = logging.getLogger(__name__)


class ChatHandler(BaseWebSocketHandler):
    """Handle real-time chat functionality for webtoon collaboration"""

    def __init__(
        self, 
        chat_service: Optional[ChatService] = None, 
        connection_manager: Optional[ConnectionManager] = None,
        room_manager = None
    ):
        """Initialize the chat handler.
        
        Args:
            chat_service: The chat service for business logic and persistence
            connection_manager: The WebSocket connection manager
            room_manager: The room manager for handling room operations
        """
        super().__init__(connection_manager=connection_manager, chat_service=chat_service)
        self.room_manager = room_manager or get_room_manager()
        self.chat_service = chat_service  # Keep for backward compatibility

    @message_handler("join_room")
    async def handle_join_room(
        self, 
        client_id: str, 
        message: Dict[str, Any], 
        websocket: Optional[WebSocket] = None
    ):
        """Handle client joining a chat room
        
        Message format:
        {
            "type": "join_room",
            "room_id": "<uuid-string>"
        }
        """
        room_id = message.get("room_id")
        if not room_id:
            await self.handle_error(
                client_id=client_id,
                message=message,
                error=WebSocketValidationError("room_id is required"),
                websocket=websocket
            )
            return

        try:
            # Try to parse as UUID to validate format and for database storage
            webtoon_id = UUID(room_id)
        except ValueError as e:
            await self.handle_error(
                client_id=client_id,
                message=message,
                error=ValueError("Invalid room_id format. Must be a valid UUID."),
                websocket=websocket
            )
            return

        # Remove client from previous room if any
        await self._leave_current_room(client_id)

        # Add client to new room using RoomManager
        try:
            # Join the new room
            await self.room_manager.join_room(client_id, room_id, websocket)
            
            # Get updated room info
            room_info = await self.room_manager.get_room_info(room_id)
            
            # Notify client of successful join
            join_message = {
                "type": "chat_room_joined",
                "room_id": room_id,
                "participants": room_info["participant_count"],
            }
            await self.connection_manager.send_personal_message(join_message, client_id)
            
            # Notify other participants
            await self.room_manager.broadcast_to_room(
                room_id,
                {
                    "type": "participant_joined",
                    "client_id": client_id,
                    "participants": room_info["participant_count"],
                },
                exclude_client=client_id
            )
            
            logger.info(f"Client {client_id} joined room {room_id}")
            
        except WebSocketValidationError as e:
            await self.handle_error(
                client_id=client_id,
                message=message,
                error=e,
                websocket=websocket
            )
            return
            
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

    @message_handler("leave_room")
    async def handle_leave_room(
        self,
        client_id: str,
        message: Dict[str, Any],
        websocket: Optional[WebSocket] = None
    ):
        """Handle client leaving a chat room
        
        Message format:
        {
            "type": "leave_room"
        }
        """
        # Get the room_id before leaving
        room_id = await self.room_manager.get_client_room(client_id)
        if not room_id:
            logger.warning(f"Client {client_id} tried to leave but was not in any room")
            return
            
        # Leave the room using RoomManager
        left_room_id = await self.room_manager.leave_room(client_id)
        
        if left_room_id:
            # Get updated room info
            try:
                room_info = await self.room_manager.get_room_info(left_room_id)
                participant_count = room_info["participant_count"]
            except WebSocketValidationError:
                # Room no longer exists (last participant)
                participant_count = 0
                
            # Notify other participants
            await self.room_manager.broadcast_to_room(
                left_room_id,
                {
                    "type": "participant_left",
                    "client_id": client_id,
                    "participants": participant_count
                },
                exclude_client=client_id
            )
            
            logger.info(f"Client {client_id} left room {left_room_id}")
        
        # Notify the client they've left the room
        await self.connection_manager.send_personal_message(
            {
                "type": "chat_room_left",
                "room_id": room_id
            },
            client_id
        )

    @message_handler("chat_message")
    async def handle_chat_message(
        self,
        client_id: str,
        message: Dict[str, Any],
        websocket: Optional[WebSocket] = None
    ):
        """Handle chat message from client
        
        Message format:
        {
            "type": "chat_message",
            "text": "message content",
            "role": "user",  # Optional, defaults to "user"
            "tool_calls": []  # Optional, for function/tool calls
        }
        """
        logger.info(f"Received chat message from client {client_id}: {message}")
        
        # Get the room_id from room manager
        room_id = await self.room_manager.get_client_room(client_id)
        if not room_id:
            logger.warning(f"Client {client_id} sent message but is not in any room")
            return
        if not room_id:
            logger.warning(f"Client {client_id} tried to send message without joining a room first")
            await self.handle_error(
                client_id=client_id,
                message=message,
                error=ValueError("You must join a room first"),
                websocket=websocket
            )
            return

        # Check for message content in either 'text' or 'content' field (for compatibility)
        chat_text = message.get("text", "").strip() or message.get("content", "").strip()
        if not chat_text:
            await self.handle_error(
                client_id=client_id,
                message=message,
                error=ValueError("Message text cannot be empty"),
                websocket=websocket
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
        await self.room_manager.broadcast_to_room(
            room_id,
            chat_message,
            exclude_client=client_id
        )

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
                    await self.room_manager.broadcast_to_room(
                        room_id, 
                        typing_indicator, 
                        exclude_client=client_id
                    )
                    
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
                        await self.room_manager.broadcast_to_room(
                            room_id, 
                            typing_indicator
                        )
                        
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
                        await self.room_manager.broadcast_to_room(
                            room_id, 
                            ai_response
                        )
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

    @message_handler("typing_indicator")
    async def handle_typing_indicator(
        self, 
        client_id: str, 
        message: Dict[str, Any], 
        websocket: Optional[WebSocket] = None
    ):
        """Handle typing indicator
        
        Message format:
        {
            "type": "typing_indicator",
            "is_typing": true
        }
        """
        room_id = await self.room_manager.get_client_room(client_id)
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
        await self.room_manager.broadcast_to_room(
            room_id, 
            typing_message, 
            exclude_client=client_id
        )

    async def handle_client_disconnect(self, client_id: str):
        """
        Handle client disconnection
        
        Args:
            client_id: The ID of the disconnecting client
        """
        # Get the room ID before leaving
        room_id = await self.room_manager.get_client_room(client_id)
        
        # Remove client from room
        left_room_id = await self.room_manager.leave_room(client_id)
        
        if left_room_id:
            # Get updated room info
            try:
                room_info = await self.room_manager.get_room_info(left_room_id)
                participant_count = room_info["participant_count"]
            except WebSocketValidationError:
                # Room no longer exists (last participant)
                participant_count = 0
                
            # Notify other participants
            await self.room_manager.broadcast_to_room(
                left_room_id,
                {
                    "type": "participant_left",
                    "client_id": client_id,
                    "participants": participant_count
                },
                exclude_client=client_id
            )
        
        # Notify the tool handler about the disconnect
        tool_handler = get_tool_handler()
        await tool_handler.handle_client_disconnect(client_id)
        
        logger.info(f"Client {client_id} disconnected from room {room_id}")

    async def _leave_current_room(self, client_id: str) -> Optional[str]:
        """
        Remove client from their current room if any
        
        Args:
            client_id: The ID of the client leaving the room
            
        Returns:
            The room_id that was left, or None if client wasn't in a room
        """
        room_id = await self.room_manager.get_client_room(client_id)
        if not room_id:
            return None
            
        # Remove client from room using RoomManager
        left_room_id = await self.room_manager.leave_room(client_id)
        
        if left_room_id:
            # Get updated room info
            try:
                room_info = await self.room_manager.get_room_info(room_id)
                participant_count = room_info["participant_count"]
            except WebSocketValidationError:
                # Room no longer exists (last participant)
                participant_count = 0
            
            # Notify other participants
            await self.room_manager.broadcast_to_room(
                room_id,
                {
                    "type": "participant_left",
                    "client_id": client_id,
                    "participants": participant_count
                },
                exclude_client=client_id
            )
            
            logger.info(f"Client {client_id} left room {left_room_id}")
            
        return left_room_id
        
    async def _broadcast_to_room(
        self, room_id: str, message: Dict[str, Any], exclude_client: str = None
    ):
        """
        Broadcast message to all clients in a room
        
        Args:
            room_id: The ID of the room to broadcast to
            message: The message to broadcast
            exclude_client: Optional client ID to exclude from the broadcast
        """
        try:
            await self.room_manager.broadcast_to_room(
                room_id,
                message,
                exclude_client=exclude_client
            )
        except WebSocketValidationError as e:
            logger.warning(f"Failed to broadcast to room {room_id}: {str(e)}")

    async def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """
        Get information about a chat room
        
        Args:
            room_id: The ID of the room to get info for
            
        Returns:
            Dictionary containing room information
        """
        try:
            room_info = await self.room_manager.get_room_info(room_id)
            return {
                "exists": True,
                "room_id": room_id,
                "participant_count": room_info["participant_count"],
                "participants": room_info["participants"],
            }
        except WebSocketValidationError:
            return {"exists": False}

    async def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """
        Get information about a client
        
        Args:
            client_id: The ID of the client to get info for
            
        Returns:
            Dictionary containing client information
        """
        room_id = await self.room_manager.get_client_room(client_id)
        return {
            "client_id": client_id,
            "current_room": room_id,
            "in_room": room_id is not None,
        }
        
    @message_handler("discover_tools")
    async def handle_tool_discovery(
        self, 
        client_id: str, 
        message: Dict[str, Any], 
        websocket: Optional[WebSocket] = None
    ):
        """Handle tool discovery request
        
        Message format:
        {
            "type": "discover_tools"
        }
        """
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
