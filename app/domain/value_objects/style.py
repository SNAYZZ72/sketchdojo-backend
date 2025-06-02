# app/domain/value_objects/style.py
"""
Art style value object
"""
from dataclasses import dataclass
from enum import Enum


class ArtStyle(Enum):
    """Available art styles for webtoon generation"""

    MANGA = "manga"
    WEBTOON = "webtoon"
    COMIC = "comic"
    ANIME = "anime"
    REALISTIC = "realistic"
    SKETCH = "sketch"
    CHIBI = "chibi"


@dataclass(frozen=True)
class StyleConfiguration:
    """Configuration for a specific art style"""

    style: ArtStyle
    color_palette: str
    line_weight: str
    shading_style: str
    composition_notes: str

    @classmethod
    def for_style(cls, style: ArtStyle) -> "StyleConfiguration":
        """Get default configuration for a style"""
        configs = {
            ArtStyle.MANGA: cls(
                style=style,
                color_palette="black_and_white",
                line_weight="bold",
                shading_style="screentone",
                composition_notes="Dynamic panels with action lines",
            ),
            ArtStyle.WEBTOON: cls(
                style=style,
                color_palette="full_color",
                line_weight="clean",
                shading_style="soft_cell",
                composition_notes="Vertical scrolling optimized panels",
            ),
            ArtStyle.COMIC: cls(
                style=style,
                color_palette="vibrant",
                line_weight="bold",
                shading_style="flat_colors",
                composition_notes="Traditional comic book layout",
            ),
            ArtStyle.ANIME: cls(
                style=style,
                color_palette="bright",
                line_weight="clean",
                shading_style="cel_shading",
                composition_notes="Anime-style expressions and effects",
            ),
            ArtStyle.REALISTIC: cls(
                style=style,
                color_palette="natural",
                line_weight="varied",
                shading_style="realistic",
                composition_notes="Photorealistic rendering",
            ),
            ArtStyle.SKETCH: cls(
                style=style,
                color_palette="monochrome",
                line_weight="loose",
                shading_style="crosshatch",
                composition_notes="Hand-drawn sketch appearance",
            ),
            ArtStyle.CHIBI: cls(
                style=style,
                color_palette="pastel",
                line_weight="soft",
                shading_style="minimal",
                composition_notes="Cute, simplified character designs",
            ),
        }
        return configs.get(style, configs[ArtStyle.WEBTOON])

    def to_prompt_text(self) -> str:
        """Convert style configuration to AI prompt text"""
        return f"{self.style.value} style, {self.color_palette} palette, {self.line_weight} lines, {self.shading_style} shading, {self.composition_notes}"
