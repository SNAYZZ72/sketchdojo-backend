"""
Integration tests for generation flow
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def test_app():
    """Create test app"""
    return create_app()


@pytest.fixture
def client(test_app):
    """Test client"""
    return TestClient(test_app)


class TestGenerationFlow:
    """Test complete generation flow"""

    @patch("app.dependencies.get_ai_provider")
    @patch("app.dependencies.get_image_generator")
    def test_complete_generation_flow(self, mock_image_gen, mock_ai, client):
        """Test complete generation flow from API to result"""
        # Mock AI provider
        mock_ai.return_value = AsyncMock()
        mock_ai.return_value.generate_story.return_value = {
            "title": "Test Story",
            "plot_summary": "A test story",
            "setting": {"location": "Test City"},
            "main_characters": [{"name": "Hero", "description": "Brave"}],
            "theme": "Adventure",
            "mood": "Exciting",
            "key_scenes": ["Opening"],
        }

        mock_ai.return_value.generate_scene_descriptions.return_value = [
            {
                "visual_description": "Hero in city",
                "characters": ["Hero"],
                "dialogue": [{"character": "Hero", "text": "Hello!"}],
                "setting": "City",
                "mood": "determined",
                "panel_size": "full",
                "camera_angle": "medium",
                "special_effects": [],
            }
        ]

        # Mock image generator
        mock_image_gen.return_value = AsyncMock()
        mock_image_gen.return_value.is_available.return_value = True
        mock_image_gen.return_value.generate_image.return_value = (
            "/path/to/image.png",
            "http://localhost:8000/static/image.png",
        )

        # Test sync generation endpoint
        response = client.get(
            "/api/v1/generation/sync-test",
            params={
                "prompt": "A hero saves the world",
                "art_style": "webtoon",
                "num_panels": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "webtoon_id" in data
        assert "panel_count" in data
        assert data["panel_count"] == 2
