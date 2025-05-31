# =============================================================================
# app/utils/formatters.py
# =============================================================================
"""
Data formatting utilities
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Format datetime to string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_string)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_progress_percentage(current: int, total: int) -> float:
    """Calculate and format progress percentage."""
    if total <= 0:
        return 0.0

    percentage = (current / total) * 100
    return round(percentage, 1)


def format_api_response(
    data: Any = None,
    message: str = "Success",
    status: str = "success",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Format standardized API response."""
    response = {"status": status, "message": message}

    if data is not None:
        response["data"] = data

    if meta:
        response["meta"] = meta

    return response


def format_error_response(
    error: str, message: str = "An error occurred", details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format standardized error response."""
    response = {"status": "error", "error": error, "message": message}

    if details:
        response["details"] = details

    return response


def format_validation_error(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format validation error response."""
    return {
        "status": "error",
        "error": "validation_error",
        "message": "Validation failed",
        "details": {"errors": errors},
    }


def format_task_progress(
    task_id: str,
    status: str,
    progress: float,
    current_step: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Format task progress response."""
    response = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if current_step:
        response["current_step"] = current_step

    if result:
        response["result"] = result

    if error:
        response["error"] = error

    return response


def format_panel_metadata(
    panel_id: str,
    generation_time: Optional[float] = None,
    model_used: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    style_settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Format panel generation metadata."""
    metadata = {"panel_id": panel_id, "generated_at": datetime.now(timezone.utc).isoformat()}

    if generation_time is not None:
        metadata["generation_time_seconds"] = generation_time
        metadata["generation_time_formatted"] = format_duration(generation_time)

    if model_used:
        metadata["model_used"] = model_used

    if prompt_tokens is not None:
        metadata["prompt_tokens"] = prompt_tokens

    if style_settings:
        metadata["style_settings"] = style_settings

    return metadata


def format_webtoon_summary(
    webtoon_id: str,
    title: str,
    panel_count: int,
    total_generation_time: Optional[float] = None,
    character_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Format webtoon summary information."""
    summary = {
        "webtoon_id": webtoon_id,
        "title": title,
        "panel_count": panel_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if total_generation_time is not None:
        summary["total_generation_time"] = format_duration(total_generation_time)

    if character_count is not None:
        summary["character_count"] = character_count

    return summary
