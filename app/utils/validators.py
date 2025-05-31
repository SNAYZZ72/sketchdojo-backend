# =============================================================================
# app/utils/validators.py
# =============================================================================
"""
Custom validation functions
"""
import re
from typing import Any, List, Optional

from pydantic import validator

from app.utils.constants import (
    ALLOWED_IMAGE_TYPES,
    MAX_DIALOGUE_LENGTH,
    MAX_PANEL_DESCRIPTION_LENGTH,
    MAX_STORY_LENGTH,
)


def validate_story_prompt(prompt: str) -> str:
    """Validate story prompt."""
    if not prompt or not prompt.strip():
        raise ValueError("Story prompt cannot be empty")

    if len(prompt) > MAX_STORY_LENGTH:
        raise ValueError(f"Story prompt too long (max {MAX_STORY_LENGTH} characters)")

    # Check for potentially harmful content
    harmful_patterns = [
        r"\b(hack|crack|exploit)\b",
        r"\b(virus|malware|trojan)\b",
        r"\b(illegal|criminal)\b",
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, prompt.lower()):
            raise ValueError("Story prompt contains inappropriate content")

    return prompt.strip()


def validate_panel_description(description: str) -> str:
    """Validate panel description."""
    if not description or not description.strip():
        raise ValueError("Panel description cannot be empty")

    if len(description) > MAX_PANEL_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Panel description too long (max {MAX_PANEL_DESCRIPTION_LENGTH} characters)"
        )

    return description.strip()


def validate_dialogue_text(text: str) -> str:
    """Validate dialogue text."""
    if len(text) > MAX_DIALOGUE_LENGTH:
        raise ValueError(f"Dialogue text too long (max {MAX_DIALOGUE_LENGTH} characters)")

    return text.strip()


def validate_color_palette(colors: List[str]) -> List[str]:
    """Validate color palette."""
    valid_colors = []

    for color in colors:
        # Support hex colors (#RGB, #RRGGBB)
        if re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", color):
            valid_colors.append(color.upper())
        # Support RGB values
        elif re.match(r"^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$", color):
            valid_colors.append(color)
        # Support named colors (basic validation)
        elif re.match(r"^[a-zA-Z]+$", color):
            valid_colors.append(color.lower())
        else:
            raise ValueError(f"Invalid color format: {color}")

    return valid_colors


def validate_image_content_type(content_type: str) -> bool:
    """Validate image content type."""
    return content_type.lower() in ALLOWED_IMAGE_TYPES


def validate_panel_count(count: int) -> int:
    """Validate panel count."""
    if count < 1:
        raise ValueError("Panel count must be at least 1")

    if count > 50:  # Reasonable upper limit
        raise ValueError("Panel count cannot exceed 50")

    return count


def validate_character_name(name: str) -> str:
    """Validate character name."""
    if not name or not name.strip():
        raise ValueError("Character name cannot be empty")

    if len(name) > 100:
        raise ValueError("Character name too long (max 100 characters)")

    # Allow letters, numbers, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z0-9\s\-']+$", name):
        raise ValueError("Character name contains invalid characters")

    return name.strip()


# Pydantic validator decorators
def story_prompt_validator(cls, v):
    """Pydantic validator for story prompts."""
    return validate_story_prompt(v)


def panel_description_validator(cls, v):
    """Pydantic validator for panel descriptions."""
    return validate_panel_description(v)


def color_palette_validator(cls, v):
    """Pydantic validator for color palettes."""
    if v is None:
        return []
    return validate_color_palette(v)
