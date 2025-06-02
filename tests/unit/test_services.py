"""
Unit tests for application services
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.services.generation_service import GenerationService
from app.application.services.webtoon_service import WebtoonService
from app.domain.entities.character import Character
from app.domain.entities.webtoon import Webtoon
from app.domain.value_objects.style import ArtStyle


class TestWebtoonService:
    """Test WebtoonService"""

    @pytest.mark.asyncio
    async def test_create_webtoon(self, webtoon_service, sample_webtoon_data):
        """Test webtoon creation"""
        webtoon_dto = await webtoon_service.create_webtoon(
            title=sample_webtoon_data["title"],
            description=sample_webtoon_data["description"],
            art_style=sample_webtoon_data["art_style"],
        )

        assert webtoon_dto.title == sample_webtoon_data["title"]
        assert webtoon_dto.description == sample_webtoon_data["description"]
        assert webtoon_dto.art_style == ArtStyle.WEBTOON
        assert webtoon_dto.panel_count == 0
        assert webtoon_dto.character_count == 0

    @pytest.mark.asyncio
    async def test_add_character_to_webtoon(self, webtoon_service):
        """Test adding character to webtoon"""
        # Create webtoon
        webtoon_dto = await webtoon_service.create_webtoon(
            title="Test", description="Test", art_style="webtoon"
        )

        # Create character
        character = Character(name="Test Hero", description="Brave protagonist")

        # Add character
        updated_dto = await webtoon_service.add_character(webtoon_dto.id, character)

        assert updated_dto is not None
        assert updated_dto.character_count == 1
        assert any(c.name == "Test Hero" for c in updated_dto.characters)


class TestGenerationService:
    """Test GenerationService"""

    @pytest.mark.asyncio
    async def test_start_webtoon_generation(
        self, generation_service, sample_generation_request
    ):
        """Test starting webtoon generation"""
        result = await generation_service.start_webtoon_generation(
            sample_generation_request
        )

        assert result.task_id is not None
        assert result.status == "pending"
        assert result.progress_percentage == 0.0

    @pytest.mark.asyncio
    async def test_generate_webtoon_sync(
        self, generation_service, sample_generation_request
    ):
        """Test synchronous webtoon generation"""
        result = await generation_service.generate_webtoon_sync(
            sample_generation_request
        )

        assert "webtoon_id" in result
        assert "title" in result
        assert "panel_count" in result
        assert result["panel_count"] == sample_generation_request.num_panels
