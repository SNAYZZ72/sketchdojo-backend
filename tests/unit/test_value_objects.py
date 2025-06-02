"""
Unit tests for domain value objects
"""
import pytest

from app.domain.value_objects.dimensions import PanelDimensions, PanelSize
from app.domain.value_objects.position import Position
from app.domain.value_objects.style import ArtStyle, StyleConfiguration


class TestArtStyle:
    """Test ArtStyle value object"""

    def test_art_style_enum(self):
        """Test art style enumeration"""
        assert ArtStyle.MANGA.value == "manga"
        assert ArtStyle.WEBTOON.value == "webtoon"
        assert ArtStyle.COMIC.value == "comic"

    def test_style_configuration(self):
        """Test style configuration creation"""
        config = StyleConfiguration.for_style(ArtStyle.MANGA)

        assert config.style == ArtStyle.MANGA
        assert config.color_palette == "black_and_white"
        assert config.line_weight == "bold"
        assert "Dynamic panels" in config.composition_notes

    def test_style_prompt_text(self):
        """Test style configuration to prompt text"""
        config = StyleConfiguration.for_style(ArtStyle.WEBTOON)
        prompt_text = config.to_prompt_text()

        assert "webtoon style" in prompt_text
        assert "full_color palette" in prompt_text


class TestPanelDimensions:
    """Test PanelDimensions value object"""

    def test_default_dimensions(self):
        """Test default panel dimensions"""
        dims = PanelDimensions()

        assert dims.size == PanelSize.FULL
        assert dims.width == 1024
        assert dims.height == 1024
        assert dims.aspect_ratio == "1:1"

    def test_dimensions_from_size(self):
        """Test creating dimensions from size"""
        half_dims = PanelDimensions.from_size(PanelSize.HALF)

        assert half_dims.size == PanelSize.HALF
        assert half_dims.width == 512
        assert half_dims.height == 1024
        assert half_dims.aspect_ratio == "1:2"

    def test_custom_dimensions(self):
        """Test custom dimensions"""
        custom_dims = PanelDimensions.custom(800, 600)

        assert custom_dims.size == PanelSize.CUSTOM
        assert custom_dims.width == 800
        assert custom_dims.height == 600
        assert custom_dims.aspect_ratio == "800:600"

    def test_total_pixels(self):
        """Test total pixel calculation"""
        dims = PanelDimensions(width=100, height=200)
        assert dims.total_pixels == 20000


class TestPosition:
    """Test Position value object"""

    def test_default_position(self):
        """Test default position"""
        pos = Position()

        assert pos.x_percent == 50.0
        assert pos.y_percent == 50.0
        assert pos.anchor == "center"

    def test_position_validation(self):
        """Test position validation"""
        with pytest.raises(ValueError):
            Position(x_percent=150)  # Over 100

        with pytest.raises(ValueError):
            Position(y_percent=-10)  # Under 0

    def test_named_positions(self):
        """Test creating positions from names"""
        top_left = Position.from_named_position("top-left")

        assert top_left.x_percent == 10
        assert top_left.y_percent == 10
        assert top_left.anchor == "top-left"

    def test_css_style_generation(self):
        """Test CSS style generation"""
        pos = Position(x_percent=25, y_percent=75)
        css = pos.to_css_style()

        assert "left: 25%" in css
        assert "top: 75%" in css

    def test_coordinate_conversion(self):
        """Test converting to absolute coordinates"""
        pos = Position(x_percent=50, y_percent=25)
        x, y = pos.to_coordinates(800, 600)

        assert x == 400  # 50% of 800
        assert y == 150  # 25% of 600
