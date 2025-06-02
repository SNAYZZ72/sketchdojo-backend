# app/utils/validators.py
"""
Input validation utilities
"""
import re
from uuid import UUID

from app.utils.exceptions import ValidationError


def validate_prompt(prompt: str) -> str:
    """Validate story prompt"""
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt cannot be empty")

    prompt = prompt.strip()
    if len(prompt) < 10:
        raise ValidationError("Prompt must be at least 10 characters long")

    if len(prompt) > 2000:
        raise ValidationError("Prompt cannot exceed 2000 characters")

    return prompt


def validate_webtoon_title(title: str) -> str:
    """Validate webtoon title"""
    if not title or not title.strip():
        raise ValidationError("Title cannot be empty")

    title = title.strip()
    if len(title) > 200:
        raise ValidationError("Title cannot exceed 200 characters")

    return title


def validate_character_name(name: str) -> str:
    """Validate character name"""
    if not name or not name.strip():
        raise ValidationError("Character name cannot be empty")

    name = name.strip()
    if len(name) > 100:
        raise ValidationError("Character name cannot exceed 100 characters")

    # Check for valid characters (letters, numbers, spaces, basic punctuation)
    if not re.match(r"^[a-zA-Z0-9\s\-_.\']+$", name):
        raise ValidationError("Character name contains invalid characters")

    return name


def validate_panel_count(count: int) -> int:
    """Validate panel count"""
    if count < 1:
        raise ValidationError("Panel count must be at least 1")

    if count > 20:
        raise ValidationError("Panel count cannot exceed 20")

    return count


def validate_uuid(uuid_str: str) -> UUID:
    """Validate UUID string"""
    try:
        return UUID(uuid_str)
    except ValueError:
        raise ValidationError(f"Invalid UUID format: {uuid_str}")


def validate_art_style(style: str) -> str:
    """Validate art style"""
    valid_styles = [
        "manga",
        "webtoon",
        "comic",
        "anime",
        "realistic",
        "sketch",
        "chibi",
    ]

    if style not in valid_styles:
        raise ValidationError(
            f"Invalid art style. Must be one of: {', '.join(valid_styles)}"
        )

    return style


def validate_panel_size(size: str) -> str:
    """Validate panel size"""
    valid_sizes = ["full", "half", "third", "quarter"]

    if size not in valid_sizes:
        raise ValidationError(
            f"Invalid panel size. Must be one of: {', '.join(valid_sizes)}"
        )

    return size
