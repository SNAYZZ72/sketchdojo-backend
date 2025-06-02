# app/application/interfaces/image_generator.py
"""
Image generator interface for AI image generation
"""
from abc import ABC, abstractmethod
from typing import Tuple


class ImageGenerator(ABC):
    """Interface for AI image generation services"""

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str = "webtoon",
    ) -> Tuple[str, str]:
        """
        Generate an image from a prompt
        Returns: (local_file_path, public_url)
        """

    @abstractmethod
    async def enhance_prompt(self, base_prompt: str, style_modifiers: str) -> str:
        """Enhance a prompt with style-specific modifiers"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the image generator is available"""
