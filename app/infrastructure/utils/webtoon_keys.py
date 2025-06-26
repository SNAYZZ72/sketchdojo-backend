"""
Redis key generation utilities for webtoon-related data.

This module provides functions to generate consistent Redis keys
for webtoon entities and related data structures.
"""
from typing import Optional, Union
from uuid import UUID

def webtoon_key(webtoon_id: Union[UUID, str]) -> str:
    """
    Generate a Redis key for a webtoon entity.

    Args:
        webtoon_id: The ID of the webtoon

    Returns:
        str: The Redis key for the webtoon
    """
    return f"webtoon:{str(webtoon_id)}"

def webtoon_list_key() -> str:
    """
    Generate a Redis key for the set of all webtoon IDs.

    Returns:
        str: The Redis key for the webtoon ID set
    """
    return "webtoons:all"

def webtoon_search_index_key() -> str:
    """
    Generate a Redis key for the webtoon search index.

    Returns:
        str: The Redis key for the search index
    """
    return "webtoon:search:index"

def webtoon_user_webtoons_key(user_id: Union[UUID, str]) -> str:
    """
    Generate a Redis key for the set of webtoon IDs belonging to a user.

    Args:
        user_id: The ID of the user

    Returns:
        str: The Redis key for the user's webtoon ID set
    """
    return f"user:{str(user_id)}:webtoons"

def webtoon_status_key(webtoon_id: Union[UUID, str]) -> str:
    """
    Generate a Redis key for a webtoon's status.

    Args:
        webtoon_id: The ID of the webtoon

    Returns:
        str: The Redis key for the webtoon's status
    """
    return f"webtoon:{str(webtoon_id)}:status"

def webtoon_episodes_key(webtoon_id: Union[UUID, str]) -> str:
    """
    Generate a Redis key for the list of episode IDs for a webtoon.

    Args:
        webtoon_id: The ID of the webtoon

    Returns:
        str: The Redis key for the webtoon's episodes list
    """
    return f"webtoon:{str(webtoon_id)}:episodes"

def webtoon_pattern() -> str:
    """
    Generate a Redis pattern to match all webtoon keys.

    Returns:
        str: The Redis pattern for webtoon keys
    """
    return "webtoon:*"

def webtoon_episodes_pattern() -> str:
    """
    Generate a Redis pattern to match all webtoon episode list keys.

    Returns:
        str: The Redis pattern for webtoon episode list keys
    """
    return "webtoon:*:episodes"

def webtoon_episode_key(webtoon_id: Union[UUID, str], episode_number: int) -> str:
    """
    Generate a Redis key for a specific webtoon episode.

    Args:
        webtoon_id: The ID of the webtoon
        episode_number: The episode number

    Returns:
        str: The Redis key for the webtoon episode
    """
    return f"webtoon:{str(webtoon_id)}:episode:{episode_number}"
