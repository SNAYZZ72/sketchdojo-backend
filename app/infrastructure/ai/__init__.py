# =============================================================================
# app/infrastructure/ai/__init__.py
# =============================================================================
"""
AI Infrastructure Package

This package provides the AI integration layer for SketchDojo, including:
- LLM clients for text generation and structured output
- Image generation clients for visual content
- Processing pipelines for story and panel creation
"""

from .image.base import BaseImageGenerator, ImageProvider, ImageRequest, ImageResponse, ImageStyle
from .image.stability_ai import StabilityAIGenerator
from .llm.base import BaseLLMClient, ChatMessage, LLMProvider, MessageRole
from .llm.openai_client import OpenAIClient
from .processors.panel_processor import PanelProcessor
from .processors.story_processor import StoryProcessor

__all__ = [
    "BaseLLMClient",
    "LLMProvider",
    "ChatMessage",
    "MessageRole",
    "OpenAIClient",
    "BaseImageGenerator",
    "ImageProvider",
    "ImageRequest",
    "ImageResponse",
    "ImageStyle",
    "StabilityAIGenerator",
    "StoryProcessor",
    "PanelProcessor",
]
