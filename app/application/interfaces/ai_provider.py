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
        pass

    @abstractmethod
    async def generate_scene_descriptions(
        self, story: Dict[str, Any], num_panels: int
    ) -> List[Dict[str, Any]]:
        """Generate scene descriptions for panels"""
        pass

    @abstractmethod
    async def generate_dialogue(
        self, scene_description: str, character_names: List[str], mood: str
    ) -> List[Dict[str, str]]:
        """Generate dialogue for characters in a scene"""
        pass

    @abstractmethod
    async def enhance_visual_description(
        self, base_description: str, art_style: str, technical_specs: Dict[str, Any]
    ) -> str:
        """Enhance a visual description for image generation"""
        pass
