# =============================================================================
# app/infrastructure/ai/image/base.py
# =============================================================================
import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    STABILITY_AI = "stability_ai"
    MIDJOURNEY = "midjourney"
    MOCK = "mock"  # For testing


class ImageStyle(str, Enum):
    """Image generation styles."""

    WEBTOON = "webtoon"
    MANGA = "manga"
    COMIC = "comic"
    REALISTIC = "realistic"
    ANIME = "anime"


class ImageQuality(str, Enum):
    """Image quality levels."""

    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


class ImageRequest(BaseModel):
    """Image generation request."""

    prompt: str
    style: ImageStyle = ImageStyle.WEBTOON
    quality: ImageQuality = ImageQuality.STANDARD
    width: int = 1024
    height: int = 1024
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    guidance_scale: float = 7.0
    steps: int = 30


class ImageResponse(BaseModel):
    """Image generation response."""

    image_url: str
    image_data: Optional[bytes] = None
    seed: Optional[int] = None
    metadata: Dict[str, Any] = {}


class BaseImageGenerator(ABC):
    """Base class for image generators."""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def generate_image(self, request: ImageRequest) -> ImageResponse:
        """Generate an image based on the request."""
        pass

    @abstractmethod
    async def upscale_image(self, image_url: str, scale_factor: int = 2) -> ImageResponse:
        """Upscale an existing image."""
        pass
