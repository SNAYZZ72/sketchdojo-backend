"""
Unit tests for AI provider
"""
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from tenacity import RetryError

from app.infrastructure.ai.data_normalizers import (
    StoryDataNormalizer,
    SceneDataNormalizer,
    DialogueDataNormalizer,
    ChatCompletionNormalizer,
)
from app.infrastructure.ai.openai_provider import OpenAIProvider
from app.infrastructure.ai.prompt_templates import PromptTemplates
from app.infrastructure.ai.utils import ai_operation


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
                "setting": {
                    "location": "Fantasy kingdom",
                    "time_period": "Medieval",
                },
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
                            {
                                "character": "Hero",
                                "text": "I must begin my quest",
                            }
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

        # Configure AsyncMock to be awaitable
        mock_create = AsyncMock()
        mock_create.return_value = mock_response

        with patch.object(
            ai_provider.client.chat.completions,
            "create",
            return_value=mock_create(),
        ):
            scenes = await ai_provider.generate_scene_descriptions(story, 1)

            assert len(scenes) == 1
            scene = scenes[0]
            assert scene["visual_description"] == "Hero stands in the village square"
            assert "Hero" in scene["characters"]
            assert scene["dialogue"][0]["character"] == "Hero"


class TestAIOperation:
    """Test ai_operation decorator"""
    
    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test that ai_operation allows successful operations to complete"""
        mock_func = AsyncMock(return_value="success")
        decorated = ai_operation(mock_func)
        result = await decorated()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_error(self):
        """Test that ai_operation retries on error"""
        mock_func = AsyncMock(side_effect=[Exception("Temporary error"), "success"])
        decorated = ai_operation(mock_func)
        result = await decorated()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that ai_operation fails after max retries"""
        mock_func = AsyncMock(side_effect=[Exception("Error")] * 4)
        decorated = ai_operation(mock_func)
        
        with pytest.raises(Exception):
            await decorated()
            
        assert mock_func.call_count == 3  # Default is 3 attempts


class TestStoryDataNormalizer:
    """Test StoryDataNormalizer"""
    
    def test_normalize_complete_data(self):
        """Test normalizing complete data"""
        data = {
            "title": "Test Story",
            "plot_summary": "A summary",
            "setting": {"location": "Fantasy land"},
            "main_characters": [
                {"name": "Hero", "description": "Brave", "role": "protagonist"}
            ],
            "theme": "Adventure",
            "mood": "Exciting",
            "key_scenes": ["Opening", "Climax"]
        }
        
        result = StoryDataNormalizer.normalize(data)
        
        assert result["title"] == "Test Story"
        assert result["plot_summary"] == "A summary"
        assert result["setting"]["location"] == "Fantasy land"
        assert result["main_characters"][0]["name"] == "Hero"
        
    def test_normalize_incomplete_data(self):
        """Test normalizing incomplete data"""
        data = {"title": "Test Story"}
        
        result = StoryDataNormalizer.normalize(data)
        
        assert result["title"] == "Test Story"
        assert result["plot_summary"] == ""
        assert isinstance(result["setting"], dict)
        assert isinstance(result["main_characters"], list)
        
    def test_normalize_malformed_characters(self):
        """Test normalizing malformed character data"""
        data = {
            "title": "Test Story",
            "main_characters": ["Hero", {"name": "Villain"}]
        }
        
        result = StoryDataNormalizer.normalize(data)
        
        assert len(result["main_characters"]) == 2
        assert result["main_characters"][0]["name"] == "Hero"
        assert result["main_characters"][0]["role"] == "character"
        assert result["main_characters"][1]["name"] == "Villain"


class TestSceneDataNormalizer:
    """Test SceneDataNormalizer"""
    
    def test_normalize_complete_scenes(self):
        """Test normalizing complete scene data"""
        scenes = [{
            "visual_description": "A forest scene",
            "characters": ["Hero", "Companion"],
            "dialogue": [
                {"character": "Hero", "text": "Let's go!"},
                {"character": "Companion", "text": "I'll follow"}
            ],
            "setting": "Deep forest",
            "mood": "mysterious",
            "panel_size": "full",
            "camera_angle": "wide",
            "special_effects": ["Mist", "Sunbeams"]
        }]
        
        result = SceneDataNormalizer.normalize(scenes)
        
        assert len(result) == 1
        assert result[0]["visual_description"] == "A forest scene"
        assert len(result[0]["characters"]) == 2
        assert len(result[0]["dialogue"]) == 2
        assert result[0]["dialogue"][0]["character"] == "Hero"
        
    def test_normalize_incomplete_scenes(self):
        """Test normalizing incomplete scene data"""
        scenes = [{"visual_description": "A scene"}]
        
        result = SceneDataNormalizer.normalize(scenes)
        
        assert result[0]["visual_description"] == "A scene"
        assert result[0]["panel_size"] == "full"  # Default value
        assert result[0]["camera_angle"] == "medium"  # Default value
        
    def test_normalize_malformed_dialogue(self):
        """Test normalizing malformed dialogue"""
        scenes = [{
            "visual_description": "A scene",
            "dialogue": ["Some text", {"character": "Hero", "text": "Hello"}]
        }]
        
        result = SceneDataNormalizer.normalize(scenes)
        
        assert len(result[0]["dialogue"]) == 2
        assert result[0]["dialogue"][0]["character"] == "Character"  # Default
        assert result[0]["dialogue"][0]["text"] == "Some text"
        assert result[0]["dialogue"][1]["character"] == "Hero"


class TestChatCompletionNormalizer:
    """Test ChatCompletionNormalizer"""
    
    def test_normalize_basic_response(self):
        """Test normalizing basic response"""
        mock_message = MagicMock()
        mock_message.content = "Test content"
        mock_message.tool_calls = None
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        result = ChatCompletionNormalizer.normalize_response(mock_response)
        
        assert result["content"] == "Test content"
        assert result["finish_reason"] == "stop"
        assert "tool_calls" not in result
    
    def test_normalize_response_with_tool_calls(self):
        """Test normalizing response with tool calls"""
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.arguments = '{"arg1": "value1", "arg2": 42}'
        
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock()
        mock_message.content = "Test content"
        mock_message.tool_calls = [mock_tool_call]
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        result = ChatCompletionNormalizer.normalize_response(mock_response)
        
        assert result["content"] == "Test content"
        assert result["finish_reason"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"
        assert result["tool_calls"][0]["name"] == "test_function"
        assert result["tool_calls"][0]["arguments"]["arg1"] == "value1"
        assert result["tool_calls"][0]["arguments"]["arg2"] == 42
    
    def test_normalize_invalid_tool_call_arguments(self):
        """Test normalizing response with invalid tool call arguments"""
        mock_function = MagicMock()
        mock_function.name = "test_function"
        mock_function.arguments = "invalid json"
        
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function
        
        mock_message = MagicMock()
        mock_message.content = "Test content"
        mock_message.tool_calls = [mock_tool_call]
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        result = ChatCompletionNormalizer.normalize_response(mock_response)
        
        assert result["tool_calls"][0]["arguments"] == "invalid json"


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
        
    def test_get_chat_system_prompt_basic(self):
        """Test basic chat system prompt without context"""
        templates = PromptTemplates()
        prompt = templates.get_chat_system_prompt()
        
        assert "creative and helpful assistant" in prompt
        assert "webtoon creation app" in prompt
        assert "Webtoon context" not in prompt
        
    def test_get_chat_system_prompt_with_context(self):
        """Test chat system prompt with webtoon context"""
        templates = PromptTemplates()
        context = {"title": "Test Webtoon", "characters": ["Character 1", "Character 2"]}
        prompt = templates.get_chat_system_prompt(context)
        
        assert "creative and helpful assistant" in prompt
        assert "Webtoon context" in prompt
        assert "Test Webtoon" in prompt
