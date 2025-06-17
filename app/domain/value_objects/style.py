# app/domain/value_objects/style.py
"""
Art style value object
"""
from dataclasses import dataclass

# Import from centralized constants file
from app.domain.constants.art_styles import (
    ArtStyle as ArtStyleLiteral,  # Import the Literal as a different name
    ArtStyleEnum,
    ensure_art_style_string
)

# Note: All ArtStyle definitions have been moved to app/domain/constants/art_styles.py
# This file now imports those definitions for backward compatibility

# Re-export ArtStyleEnum as ArtStyle to maintain backward compatibility with existing code
ArtStyle = ArtStyleEnum  # This makes ArtStyle.WEBTOON work again


@dataclass(frozen=True)
class StyleConfiguration:
    """Configuration for a specific art style"""

    style: str
    color_palette: str
    line_weight: str
    shading_style: str
    composition_notes: str

    @classmethod
    def for_style(cls, style: str) -> "StyleConfiguration":
        """Get default configuration for a style"""
        configs = {
            "manga": cls(
                style=style,
                color_palette="black_and_white",
                line_weight="bold",
                shading_style="screentone",
                composition_notes="Dynamic panels with action lines",
            ),
            "webtoon": cls(
                style=style,
                color_palette="full_color",
                line_weight="clean",
                shading_style="soft_cell",
                composition_notes="Vertical scrolling optimized panels",
            ),
            "comic": cls(
                style=style,
                color_palette="primary_colors",
                line_weight="variable",
                shading_style="hatching",
                composition_notes="Traditional comic book panel layout",
            ),
            "anime": cls(
                style=style,
                color_palette="vibrant",
                line_weight="crisp",
                shading_style="cel",
                composition_notes="Expressive character close-ups",
            ),
            "realistic": cls(
                style=style,
                color_palette="natural",
                line_weight="subtle",
                shading_style="realistic",
                composition_notes="Cinematic framing and lighting",
            ),
            "sketch": cls(
                style=style,
                color_palette="monochrome",
                line_weight="loose",
                shading_style="crosshatch",
                composition_notes="Hand-drawn sketch appearance",
            ),
            "chibi": cls(
                style=style,
                color_palette="pastel",
                line_weight="soft",
                shading_style="minimal",
                composition_notes="Cute, simplified character designs",
            ),
        }
        return configs.get(style.lower(), configs["webtoon"])

    def to_prompt_text(self) -> str:
        """Convert style configuration to AI prompt text"""
        return f"{self.style} style, {self.color_palette} palette, {self.line_weight} lines, {self.shading_style} shading, {self.composition_notes}"
