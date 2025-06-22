"""
Utility functions for AI providers
"""
import functools
import logging
from typing import Any, Callable, TypeVar, cast

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar("T")


def ai_operation(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for AI operations that adds error handling and retry logic
    
    This decorator:
    1. Adds retry logic with exponential backoff
    2. Provides consistent error logging
    3. Ensures proper exception propagation
    """
    @functools.wraps(func)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            operation_name = func.__name__
            logger.debug(f"Starting AI operation: {operation_name}")
            result = await func(*args, **kwargs)
            logger.debug(f"Successfully completed AI operation: {operation_name}")
            return result
        except Exception as e:
            logger.error(f"Error in AI operation {func.__name__}: {str(e)}")
            raise
    
    return cast(Callable[..., T], wrapped)
