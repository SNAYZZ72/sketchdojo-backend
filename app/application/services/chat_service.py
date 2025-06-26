# app/application/services/chat_service.py
"""
Chat business logic service
"""
import logging
import json
from datetime import UTC, datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from app.application.interfaces.ai_provider import AIProvider
from app.application.services.base_service import BaseService
from app.core.error_handling.base_error_handler import BaseErrorHandler
from app.domain.entities.chat import ChatMessage, ChatRoom, ToolCall
from app.domain.repositories.chat_repository import ChatRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.infrastructure.ai.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class ToolProvider:
    """Provider for tools that can be used in AI interactions"""
    
    @staticmethod
    def get_available_tools() -> List[Dict]:
        """Get the tools available for the AI to use"""
        from app.websocket.handlers.tool_handler import get_tool_handler
        
        # Get all tools from the tool handler
        tool_handler = get_tool_handler()
        available_tools = tool_handler.tool_registry.list_tools()
        
        # Filter out tools that aren't relevant for the AI
        excluded_tools = ["echo", "weather"]
        filtered_tools = [tool for tool in available_tools if tool["tool_id"] not in excluded_tools]
        
        return filtered_tools
        
    @staticmethod
    def format_tools_for_ai_provider(tools: List[Dict]) -> List[Dict]:
        """Format tools in a structure suitable for the AI provider"""
        formatted_tools = []
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"].lower().replace(" ", "_"),
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return formatted_tools


class ChatMessageFormatter:
    """Formats chat messages for AI provider interactions"""
    
    @staticmethod
    def format_messages_for_ai_provider(messages: List[ChatMessage]) -> List[Dict]:
        """Format chat messages for the AI provider"""
        formatted_messages = []
        
        for msg in messages:
            # First add the message
            message_content = {
                "role": msg.role,
                "content": msg.content
            }
            
            # If message has tool calls, add them
            if msg.tool_calls and msg.role == "assistant":
                message_content["tool_calls"] = [{
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments
                } for tc in msg.tool_calls]
            
            # Add the main message first
            formatted_messages.append(message_content)
            
            # Then add any tool results as separate function messages AFTER the assistant message
            if msg.tool_calls and msg.role == "assistant":
                tool_results = [tc for tc in msg.tool_calls if tc.status == "succeeded" and tc.result]
                for tc in tool_results:
                    formatted_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tc.result) if isinstance(tc.result, dict) else tc.result
                    })
                    
        return formatted_messages


class ChatService(BaseService):
    """Service for chat business operations"""
    
    def __init__(self, 
                repository: ChatRepository, 
                ai_provider: Optional[AIProvider] = None,
                webtoon_repository: Optional[WebtoonRepository] = None,
                error_handler: Optional[BaseErrorHandler] = None,
                logger: Optional[logging.Logger] = None
    ):
        """Initialize the chat service.
        
        Args:
            repository: The chat repository for data access
            ai_provider: Optional AI provider for generating responses
            webtoon_repository: Optional repository for webtoon data
            error_handler: Optional error handler instance
            logger: Optional logger instance
        """
        # Initialize with the provided logger or create a new one
        super().__init__(error_handler=error_handler, logger=logger or logging.getLogger(__name__))
        self.repository = repository
        self.ai_provider = ai_provider
        self.webtoon_repository = webtoon_repository

    async def create_message(
        self,
        webtoon_id: UUID,
        client_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
    ) -> ChatMessage:
        """
        Create a new chat message
        
        Args:
            webtoon_id: The ID of the webtoon this message belongs to
            client_id: The client ID that sent the message
            role: The role of the message sender (user, assistant, system)
            content: The message content
            message_id: Optional external message ID for tracking
            tool_calls: Optional list of tool calls in the message
            
        Returns:
            The created chat message entity
        """
        # Create tool call objects if provided
        tool_call_objects = []
        if tool_calls:
            for tc in tool_calls:
                tool_call_objects.append(
                    ToolCall(
                        id=tc.get("id", str(uuid4())),
                        name=tc.get("name", ""),
                        arguments=tc.get("arguments", {}),
                        status=tc.get("status", "pending"),
                        result=tc.get("result"),
                        error=tc.get("error"),
                    )
                )
        
        # Create message entity
        message = ChatMessage(
            webtoon_id=webtoon_id,
            client_id=client_id,
            role=role,
            content=content,
            message_id=message_id if message_id else f"msg_{str(uuid4())}",
            tool_calls=tool_call_objects,
            timestamp=datetime.now(UTC),
        )
        
        # Save using repository
        saved_message = await self.repository.create(message)
        
        logger.info(f"Created chat message for webtoon {webtoon_id} from client {client_id}")
        return saved_message

    async def get_chat_history(
        self, webtoon_id: UUID, limit: int = 100, skip: int = 0
    ) -> List[ChatMessage]:
        """
        Get chat history for a webtoon
        
        Args:
            webtoon_id: The ID of the webtoon to get chat history for
            limit: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)
            
        Returns:
            List of chat messages
        """
        messages = await self.repository.get_by_webtoon_id(webtoon_id, limit, skip)
        return messages

    async def get_chat_room(self, webtoon_id: UUID) -> ChatRoom:
        """
        Get or create a chat room for a webtoon
        
        Args:
            webtoon_id: The ID of the webtoon
            
        Returns:
            Chat room entity
        """
        room = await self.repository.get_chat_room_by_webtoon_id(webtoon_id)
        if not room:
            # If room doesn't exist, create a default one
            room = ChatRoom(
                webtoon_id=webtoon_id,
                name=f"Chat for Webtoon {str(webtoon_id)[:8]}",
            )
            # The repository implementation should handle saving this
        
        return room

    async def generate_ai_response(self, webtoon_id: UUID, limit: int = 20) -> Optional[ChatMessage]:
        """
        Generate an AI assistant response based on chat history
        
        Args:
            webtoon_id: The ID of the webtoon/chat room
            limit: Maximum number of previous messages to include in context
            
        Returns:
            A new chat message from the AI assistant, or None if generation fails
        """
        try:
            self.logger.info(f"Generating AI response for webtoon_id: {webtoon_id}")
            
            # Get chat history for context
            messages = await self.get_chat_history(webtoon_id, limit=limit)
            
            # Add system prompt with webtoon context if available
            prompt_templates = PromptTemplates()
            webtoon_context = await self._get_webtoon_context(webtoon_id)
            system_prompt = prompt_templates.get_chat_system_prompt(webtoon_context=webtoon_context) if webtoon_context else prompt_templates.get_chat_system_prompt()
            
            # Format messages for the AI provider
            formatted_messages = ChatMessageFormatter.format_messages_for_ai_provider(messages)
            
            # Add system prompt if not already present
            if not any(msg.get('role') == 'system' for msg in formatted_messages):
                formatted_messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Get available tools
            tools = ToolProvider.get_available_tools()
            
            # Generate response using AI provider
            response = await self.ai_provider.generate_chat_completion(
                messages=formatted_messages,
                tools=ToolProvider.format_tools_for_ai_provider(tools) if tools else None
            )
            
            # Create assistant message from response
            if response and 'content' in response and response['content']:
                ai_message = await self.create_message(
                    webtoon_id=webtoon_id,
                    client_id="system",
                    role="assistant",
                    content=response['content'],
                    tool_calls=response.get('tool_calls')
                )
                self.logger.info(f"Successfully generated AI response for webtoon_id: {webtoon_id}")
                return ai_message
                
            self.logger.warning(f"Empty AI response for webtoon_id: {webtoon_id}")
            return None
                
        except Exception as e:
            error_context = {
                "webtoon_id": str(webtoon_id),
                "limit": limit
            }
            self.handle_error(e, context=error_context)
            logger.exception("Exception details:")
            # Create error message on failure
            return await self.create_message(
                webtoon_id=webtoon_id,
                client_id="system",
                role="assistant",
                content="I'm sorry, I encountered an error while processing your request. Please try again."
            )
    
    async def update_tool_call_status(
        self,
        message_id: UUID,
        tool_call_id: str,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> Optional[ChatMessage]:
        """
        Update the status of a tool call in a message
        
        Args:
            message_id: The ID of the message containing the tool call
            tool_call_id: The ID of the tool call to update
            status: New status (executing, succeeded, failed)
            result: Optional result data if the tool call succeeded
            error: Optional error message if the tool call failed
            
        Returns:
            Updated chat message or None if not found
        """
        # Get the message
        message = await self.repository.get_by_id(message_id)
        if not message:
            logger.error(f"Message {message_id} not found for tool call update")
            return None
            
        # Find and update the tool call
        for tc in message.tool_calls:
            if tc.id == tool_call_id:
                tc.status = status
                if result is not None:
                    tc.result = result
                if error is not None:
                    tc.error = error
                break
        else:
            # Tool call not found
            logger.error(f"Tool call {tool_call_id} not found in message {message_id}")
            return None
            
        # Update the message
        updated_message = await self.repository.update(
            message.id, {"tool_calls": message.tool_calls}
        )
        
        # If all tool calls are completed (succeeded or failed), continue the agent loop
        all_completed = all(tc.status in ["succeeded", "failed"] for tc in updated_message.tool_calls)
        if all_completed and message.client_id == "ai_assistant":
            logger.info(f"All tool calls in message {message_id} are completed. Generating follow-up response.")
            # Continue the agent loop with the results of the tool calls
            webtoon_id = message.webtoon_id
            # Generate a new AI response that will include the tool call results
            await self.generate_ai_response(webtoon_id=webtoon_id)
        
        return updated_message
        
    async def _get_webtoon_context(self, webtoon_id: UUID) -> Dict[str, Any]:
        """
        Get context information about a webtoon for the AI
        
        Args:
            webtoon_id: The ID of the webtoon
            
        Returns:
            Dict containing webtoon context information with JSON-serializable values
        """
        def make_serializable(obj):
            """Recursively make an object JSON-serializable"""
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple, set)):
                return [make_serializable(x) for x in obj]
            if hasattr(obj, 'isoformat'):  # Handle datetime
                return obj.isoformat()
            if hasattr(obj, '__dict__'):
                return make_serializable(obj.__dict__)
            return str(obj)

        context = {"webtoon_id": str(webtoon_id)}
        
        # If we have a webtoon repository, fetch more detailed information
        if self.webtoon_repository:
            try:
                webtoon = await self.webtoon_repository.get_by_id(webtoon_id)
                if webtoon:
                    # Only include attributes that exist on the Webtoon model
                    webtoon_context = {
                        "title": str(getattr(webtoon, 'title', '')),  # Ensure string
                        "description": str(getattr(webtoon, 'description', '')),  # Ensure string
                        "art_style": str(getattr(webtoon, 'art_style', '')),  # Ensure string
                        "is_published": bool(getattr(webtoon, 'is_published', False)),  # Ensure bool
                        "panel_count": int(getattr(webtoon, 'panel_count', 0)),  # Ensure int
                        "character_count": int(getattr(webtoon, 'character_count', 0))  # Ensure int
                    }
                    
                    # Safely get metadata if it exists and make it serializable
                    metadata = getattr(webtoon, 'metadata', {})
                    if isinstance(metadata, dict):
                        webtoon_context.update(make_serializable(metadata))
                    
                    context.update(webtoon_context)
                    
            except Exception as e:
                logger.warning(f"Error getting webtoon context: {str(e)}", exc_info=True)
                # Continue with basic context
        
        return context


# Factory function to get a ChatService instance
def get_chat_service(
    repository: ChatRepository, 
    ai_provider: Optional[AIProvider] = None,
    webtoon_repository: Optional[WebtoonRepository] = None,
    error_handler: Optional[BaseErrorHandler] = None,
    logger: Optional[logging.Logger] = None
) -> ChatService:
    """
    Get a configured ChatService instance
    
    Args:
        repository: The chat repository to use
        ai_provider: Optional AI provider for generating responses
        webtoon_repository: Optional repository for accessing webtoon data
        error_handler: Optional error handler instance
        logger: Optional logger instance
        
    Returns:
        ChatService instance
    """
    return ChatService(
        repository=repository,
        ai_provider=ai_provider,
        webtoon_repository=webtoon_repository,
        error_handler=error_handler,
        logger=logger
    )
