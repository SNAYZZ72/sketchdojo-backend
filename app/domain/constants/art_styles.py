# app/domain/constants/art_styles.py
"""
Centralized definition of art styles to ensure consistency across the application.
This file is the single source of truth for art style definitions.
"""
from enum import Enum
from typing import Literal, List, Final

# Define the list of valid art styles
VALID_ART_STYLES: Final[List[str]] = [
    "webtoon",
    "manga",
    "comic",
    "anime",
    "realistic",
    "sketch",
    "chibi",
    "painting"  # Added to maintain backward compatibility
]

# Define ArtStyle as a Literal type for better type checking and JSON serialization
ArtStyle = Literal[
    "webtoon",
    "manga", 
    "comic",
    "anime", 
    "realistic", 
    "sketch", 
    "chibi",
    "painting"
]

# ArtStyleEnum for cases where enum functionality is needed
class ArtStyleEnum(str, Enum):
    """Art style enum that inherits from str for better JSON serialization"""
    WEBTOON = "webtoon"
    MANGA = "manga"
    COMIC = "comic"
    ANIME = "anime"
    REALISTIC = "realistic"
    SKETCH = "sketch"
    CHIBI = "chibi"
    PAINTING = "painting"
    
    @classmethod
    def from_str(cls, value: str) -> 'ArtStyleEnum':
        """Convert string to enum, with better error handling"""
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = ", ".join([e.value for e in cls])
            raise ValueError(f"'{value}' is not a valid ArtStyle. Valid values are: {valid_values}")
    
    @classmethod
    def to_string(cls, value: 'ArtStyleEnum') -> str:
        """Safely convert an enum to string, handling both string and enum inputs"""
        if isinstance(value, str):
            return value
        return value.value

# Helper function to ensure art_style is always a string
def ensure_art_style_string(art_style) -> str:
    """
    Convert any art_style value to a string representation.
    
    This handles the following cases:
    - ArtStyleEnum instances
    - String literals from ArtStyle type
    - String values
    - Any other object with a .value attribute
    
    Returns a string or raises ValueError for invalid styles.
    """
    if isinstance(art_style, str):
        if art_style.lower() in [s.lower() for s in VALID_ART_STYLES]:
            return art_style.lower()
        raise ValueError(f"'{art_style}' is not a valid art style")
    
    if isinstance(art_style, ArtStyleEnum):
        return art_style.value
        
    if hasattr(art_style, 'value'):
        return ensure_art_style_string(art_style.value)
    
    # Final fallback
    art_style_str = str(art_style)
    if art_style_str.lower() in [s.lower() for s in VALID_ART_STYLES]:
        return art_style_str.lower()
    
    raise ValueError(f"'{art_style_str}' is not a valid art style")
