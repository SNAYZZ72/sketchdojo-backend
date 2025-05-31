# =============================================================================
# app/utils/helpers.py
# =============================================================================
"""
Helper utility functions
"""
import hashlib
import mimetypes
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_filename(original_filename: str, prefix: str = None) -> str:
    """Generate a unique filename with timestamp and UUID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uuid_part = str(uuid.uuid4())[:8]

    # Get file extension
    path = Path(original_filename)
    extension = path.suffix.lower()

    # Clean original name
    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", path.stem)

    if prefix:
        return f"{prefix}_{timestamp}_{uuid_part}_{clean_name}{extension}"
    else:
        return f"{timestamp}_{uuid_part}_{clean_name}{extension}"


def get_file_hash(content: bytes, algorithm: str = "sha256") -> str:
    """Generate hash of file content."""
    hash_func = hashlib.new(algorithm)
    hash_func.update(content)
    return hash_func.hexdigest()


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """Validate username format."""
    # 3-50 characters, alphanumeric and underscores only
    pattern = r"^[a-zA-Z0-9_]{3,50}$"
    return re.match(pattern, username) is not None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r"_{2,}", "_", sanitized)
    # Trim underscores from ends
    sanitized = sanitized.strip("_")
    # Ensure reasonable length
    if len(sanitized) > 255:
        path = Path(sanitized)
        stem = path.stem[:250]
        sanitized = stem + path.suffix
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def parse_content_range(content_range: str) -> Dict[str, int]:
    """Parse HTTP Content-Range header."""
    # Format: bytes start-end/total
    match = re.match(r"bytes (\d+)-(\d+)/(\d+)", content_range)
    if match:
        return {
            "start": int(match.group(1)),
            "end": int(match.group(2)),
            "total": int(match.group(3)),
        }
    return {}


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_get(dictionary: Dict[str, Any], keys: str, default: Any = None) -> Any:
    """Get nested dictionary value using dot notation."""
    keys_list = keys.split(".")
    for key in keys_list:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first/last few characters."""
    if len(data) <= visible_chars * 2:
        return "*" * len(data)

    return data[:visible_chars] + "*" * (len(data) - visible_chars * 2) + data[-visible_chars:]
