"""
Unit tests for AI provider
"""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.ai.openai_provider import OpenAIProvider
from app.infrastructure.ai.prompt_templates import PromptTemplates


class TestOpenAIProvider:
    """Test OpenAI provider implementation"""

    @pytest.fixture
    def ai_provider(self):
        """Create AI provider for testing"""
        return OpenAIProvider(api_key="test-key", model="gpt-4o-mini")

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response"""
        mock_choice = AsyncMock()
        mock_message = AsyncMock()
        mock_message.content = json.dumps(
            {
                "title": "Test Story",
                "plot_summary": "A brave hero saves the world",
                "setting": {"location": "Fantasy kingdom", "time_period": "Medieval"},
                "main_characters": [
                    {
                        "name": "Hero",
                        "description": "Brave warrior",
                        "role": "protagonist",
                    }
                ],
                "theme": "Good vs Evil",
                "mood": "Heroic",
                "key_scenes": ["Hero's journey begins", "Final battle"],
            }
        )
        mock_choice.message = mock_message
        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]
        return mock_response

    @pytest.mark.asyncio
    async def test_generate_story(self, ai_provider, mock_openai_response):
        """Test story generation"""
        # Configure AsyncMock to be awaitable
        mock_create = AsyncMock()
        mock_create.return_value = mock_openai_response
        
        with patch.object(
            ai_provider.client.chat.completions,
            "create",
            return_value=mock_create(),
        ):
            story = await ai_provider.generate_story(
                "A brave hero saves the world", "fantasy"
            )

            assert story["title"] == "Test Story"
            assert story["plot_summary"] == "A brave hero saves the world"
            assert len(story["main_characters"]) == 1
            assert story["main_characters"][0]["name"] == "Hero"

    @pytest.mark.asyncio
    async def test_generate_scene_descriptions(self, ai_provider):
        """Test scene description generation"""
        story = {
            "title": "Test Story",
            "main_characters": [{"name": "Hero"}],
            "key_scenes": ["Opening scene"],
        }

        # Create mock response objects
        mock_choice = AsyncMock()
        mock_message = AsyncMock()
        mock_message.content = json.dumps(
            {
                "scenes": [
                    {
                        "visual_description": "Hero stands in the village square",
                        "characters": ["Hero"],
                        "dialogue": [
                            {"character": "Hero", "text": "I must begin my quest"}
                        ],
                        "setting": "Village square",
                        "mood": "determined",
                        "panel_size": "full",
                        "camera_angle": "medium",
                        "special_effects": [],
                    }
                ]
            }
        )
        mock_choice.message = mock_message
        mock_response = AsyncMock()
        mock_response.choices = [mock_choice]
        
        # Configure AsyncMock to be awaitable
        mock_create = AsyncMock()
        mock_create.return_value = mock_response

        with patch.object(
            ai_provider.client.chat.completions, "create", return_value=mock_create()
        ):
            scenes = await ai_provider.generate_scene_descriptions(story, 1)

            assert len(scenes) == 1
            scene = scenes[0]
            assert scene["visual_description"] == "Hero stands in the village square"
            assert "Hero" in scene["characters"]
            assert scene["dialogue"][0]["character"] == "Hero"


class TestPromptTemplates:
    """Test prompt templates"""

    def test_story_generation_prompt(self):
        """Test story generation prompt"""
        templates = PromptTemplates()
        prompt = templates.get_story_generation_prompt("webtoon")

        assert "webtoon story writer" in prompt
        assert "JSON" in prompt
        assert "main_characters" in prompt

    def test_scene_generation_prompt(self):
        """Test scene generation prompt"""
        templates = PromptTemplates()
        prompt = templates.get_scene_generation_prompt()

        assert "visual storyteller" in prompt
        assert "webtoon panels" in prompt
        assert "visual_description" in prompt

    def test_format_story_request(self):
        """Test formatting story request"""
        templates = PromptTemplates()
        request = templates.format_story_request(
            "A brave hero", "Additional context about magic"
        )

        assert "A brave hero" in request
        assert "Additional context about magic" in request
