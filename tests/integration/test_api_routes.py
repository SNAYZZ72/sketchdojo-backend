"""
Integration tests for API routes
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Test client for API testing"""
    app = create_app()
    return TestClient(app)


class TestHealthRoutes:
    """Test health check routes"""

    def test_basic_health_check(self, client):
        """Test basic health check"""
        response = client.get("/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "SketchDojo API"


class TestGenerationRoutes:
    """Test generation routes"""

    def test_sync_generation_endpoint(self, client, monkeypatch):
        """Test synchronous generation endpoint"""
        # Define our mock result
        mock_result = {
            "webtoon_id": "test-id",
            "title": "Test Webtoon",
            "panel_count": 4,
        }

        # Create a mock service with a mocked generate_webtoon_sync method
        class MockGenerationService:
            async def generate_webtoon_sync(self, *args, **kwargs):
                return mock_result

        # Replace the dependency directly
        mock_service = MockGenerationService()

        def _get_mocked_generation_service(*args, **kwargs):
            return mock_service

        # Apply the monkeypatch to the dependency function
        monkeypatch.setattr(
            "app.dependencies.get_generation_service", _get_mocked_generation_service
        )

        # Now make the request
        response = client.get(
            "/api/v1/generation/sync-test",
            params={
                "prompt": "A brave hero's adventure",
                "art_style": "webtoon",
                "num_panels": 4,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "webtoon_id" in data
        assert data["title"] == "Test Webtoon"
