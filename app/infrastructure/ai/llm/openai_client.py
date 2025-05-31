# =============================================================================
# app/infrastructure/ai/llm/openai_client.py
# =============================================================================
import json
import logging
from typing import Any, Dict, List, Optional

import openai

from .base import BaseLLMClient, ChatMessage, LLMResponse, MessageRole

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.client = openai.AsyncOpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI client with model: {model}")

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate chat completion using OpenAI API."""
        try:
            # Convert our message format to OpenAI format
            openai_messages = [{"role": msg.role.value, "content": msg.content} for msg in messages]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.model_dump() if response.usage else None,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {str(e)}")
            raise

    async def generate_structured_output(
        self, prompt: str, schema: Dict[str, Any], temperature: float = 0.3, **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI function calling."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates structured data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "generate_structured_data",
                            "description": "Generate structured data based on the schema",
                            "parameters": schema,
                        },
                    }
                ],
                tool_choice={"type": "function", "function": {"name": "generate_structured_data"}},
                temperature=temperature,
                **kwargs,
            )

            tool_call = response.choices[0].message.tool_calls[0]
            result = json.loads(tool_call.function.arguments)

            logger.debug(f"Generated structured output: {result}")
            return result
        except Exception as e:
            logger.error(f"OpenAI structured generation error: {str(e)}")
            raise
