# =============================================================================
# app/infrastructure/ai/llm/base.py
# =============================================================================
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # For testing


class MessageRole(str, Enum):
    """Message roles for chat completion."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Chat message for LLM conversation."""

    role: MessageRole
    content: str


class LLMResponse(BaseModel):
    """Response from LLM."""

    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion."""
        pass

    @abstractmethod
    async def generate_structured_output(
        self, prompt: str, schema: Dict[str, Any], temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output based on JSON schema."""
        pass
