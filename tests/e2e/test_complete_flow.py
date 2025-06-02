"""
End-to-end tests for complete generation flow
"""

import pytest

from app.application.dto.generation_dto import GenerationRequestDTO
from app.domain.value_objects.style import ArtStyle


class TestCompleteGenerationFlow:
    """Test complete generation flow from request to result"""

    @pytest.mark.asyncio
    async def test_full_webtoon_generation(
        self, generation_service, mock_ai_provider, mock_image_generator
    ):
        """Test full webtoon generation flow"""
        # Create generation request
        request = GenerationRequestDTO(
            prompt="A cyberpunk detective solves a mystery in Neo-Tokyo",
            art_style=ArtStyle.WEBTOON,
            num_panels=3,
            character_descriptions=["Detective with cybernetic implants"],
            additional_context="Dark, neon-lit atmosphere",
        )

        # Run generation
        result = await generation_service.generate_webtoon_sync(request)

        # Verify result structure
        assert "webtoon_id" in result
        assert "title" in result
        assert "panel_count" in result
        assert result["panel_count"] == 3

        # Verify AI provider was called
        mock_ai_provider.generate_story.assert_called_once()
        mock_ai_provider.generate_scene_descriptions.assert_called_once()

        # Verify image generator was called if available
        if mock_image_generator.is_available():
            assert mock_image_generator.generate_image.call_count == 3  # One per panel
