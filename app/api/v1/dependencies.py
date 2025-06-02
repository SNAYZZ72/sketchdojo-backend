# app/api/v1/dependencies.py
"""
Route-specific dependencies for API v1
"""
from typing import Dict
from uuid import UUID

from fastapi import Header, HTTPException

from app.utils.validators import validate_uuid


async def get_correlation_id(
    x_correlation_id: str = Header(None, alias="X-Correlation-ID")
) -> str:
    """Get or generate correlation ID from headers"""
    if x_correlation_id:
        return x_correlation_id

    # If not provided, generate one (this should be handled by middleware)
    import uuid

    return str(uuid.uuid4())


async def validate_task_id(task_id: str) -> UUID:
    """Validate and convert task ID parameter"""
    try:
        return validate_uuid(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")


async def validate_webtoon_id(webtoon_id: str) -> UUID:
    """Validate and convert webtoon ID parameter"""
    try:
        return validate_uuid(webtoon_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webtoon ID format")


async def get_pagination_params(page: int = 1, size: int = 20) -> Dict[str, int]:
    """Get and validate pagination parameters"""
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")

    if size < 1 or size > 100:
        raise HTTPException(status_code=400, detail="Size must be between 1 and 100")

    return {"page": page, "size": size}
