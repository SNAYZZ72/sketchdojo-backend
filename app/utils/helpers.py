# app/utils/helpers.py
"""
General helper functions
"""
import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def generate_correlation_id() -> str:
    """Generate a correlation ID for request tracing"""
    return secrets.token_hex(16)


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_string(text: str, salt: Optional[str] = None) -> str:
    """Hash a string with optional salt"""
    if salt:
        text = f"{text}{salt}"
    return hashlib.sha256(text.encode()).hexdigest()


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return dictionary.get(key, default)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def clean_filename(filename: str) -> str:
    """Clean filename for safe storage"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")

    # Ensure not empty
    if not filename:
        filename = "unnamed"

    return filename


def format_bytes(bytes_count: int) -> str:
    """Format byte count to human readable string"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Filter out None values from dictionary"""
    return {k: v for k, v in data.items() if v is not None}


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]
