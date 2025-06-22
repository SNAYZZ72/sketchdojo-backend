# app/application/interfaces/ai_provider.py
"""
AI provider interface for language model interactions
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIProvider(ABC):
    """Interface for AI language model providers"""

    @abstractmethod
    async def generate_story(
        self, prompt: str, style: str, additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a story structure from a prompt"""

    @abstractmethod
    async def generate_scene_descriptions(
        self, story: Dict[str, Any], num_panels: int
    ) -> List[Dict[str, Any]]:
        """Generate scene descriptions for panels"""

    @abstractmethod
    async def generate_dialogue(
        self, scene_description: str, character_names: List[str], mood: str
    ) -> List[Dict[str, str]]:
        """Generate dialogue for characters in a scene"""

    @abstractmethod
    async def enhance_visual_description(
        self,
        base_description: str,
        art_style: str,
        technical_specs: Dict[str, Any],
    ) -> str:
        """Enhance a visual description for image generation"""
        
    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        webtoon_context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a chat completion from a series of messages"""
