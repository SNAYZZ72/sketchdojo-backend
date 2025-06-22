# app/infrastructure/ai/openai_provider.py
"""
OpenAI provider implementation
"""
import json
import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.application.interfaces.ai_provider import AIProvider
from app.infrastructure.ai.data_normalizers import (
    ChatCompletionNormalizer,
    DialogueDataNormalizer,
    SceneDataNormalizer,
    StoryDataNormalizer,
)
from app.infrastructure.ai.prompt_templates import PromptTemplates
from app.infrastructure.ai.utils import ai_operation

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI implementation of AI provider interface"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ):
        """
        Initialize the OpenAI provider
        
        Args:
            api_key: OpenAI API key
            model: The model to use (e.g., 'gpt-4o-mini')
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum tokens in completion
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.templates = PromptTemplates()

        logger.info(f"Initialized OpenAI provider with model: {model}")

    @ai_operation
    async def generate_story(
        self, prompt: str, style: str, additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a story structure from a prompt"""
        # Get prompts
        system_prompt = self.templates.get_story_generation_prompt(style)
        user_prompt = self.templates.format_story_request(prompt, additional_context)

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )

        # Parse and normalize response
        content = response.choices[0].message.content
        story_data = json.loads(content)
        return StoryDataNormalizer.normalize(story_data)

    @ai_operation
    async def generate_scene_descriptions(
        self, story: Dict[str, Any], num_panels: int
    ) -> List[Dict[str, Any]]:
        """Generate scene descriptions for panels"""
        # Get prompts
        system_prompt = self.templates.get_scene_generation_prompt()
        user_prompt = self.templates.format_scene_request(story, num_panels)

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )

        # Parse and normalize response
        content = response.choices[0].message.content
        scenes_data = json.loads(content)
        return SceneDataNormalizer.normalize(scenes_data.get("scenes", []))

    @ai_operation
    async def generate_dialogue(
        self, scene_description: str, character_names: List[str], mood: str
    ) -> List[Dict[str, str]]:
        """Generate dialogue for characters in a scene"""
        # Get prompts
        system_prompt = self.templates.get_dialogue_generation_prompt()
        user_prompt = self.templates.format_dialogue_request(
            scene_description, character_names, mood
        )

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )

        # Parse and normalize response
        content = response.choices[0].message.content
        dialogue_data = json.loads(content)
        return DialogueDataNormalizer.normalize(dialogue_data)

    @ai_operation
    async def enhance_visual_description(
        self,
        base_description: str,
        art_style: str,
        technical_specs: Dict[str, Any],
    ) -> str:
        """Enhance a visual description for image generation"""
        # Get prompts
        system_prompt = self.templates.get_visual_enhancement_prompt(art_style)
        user_prompt = self.templates.format_visual_enhancement_request(
            base_description, technical_specs
        )

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,  # Higher temperature for creative descriptions
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    @ai_operation
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        webtoon_context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a chat completion from a series of messages"""
        # Prepare system message with webtoon context if available
        system_content = self.templates.get_chat_system_prompt(webtoon_context)
            
        # Prepare API call parameters
        params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
                *messages  # Add all conversation messages
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # Add tools parameter if provided
        if tools:
            params["tools"] = tools
            
        # Call OpenAI API
        response = await self.client.chat.completions.create(**params)
        
        # Normalize response
        result = ChatCompletionNormalizer.normalize_response(response)
        logger.info("Generated chat completion successfully")
        return result
