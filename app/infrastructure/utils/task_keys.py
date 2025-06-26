"""
Key generation utilities for task-related Redis keys.
"""
from typing import Union
from uuid import UUID

from .key_generator import KeyGenerator


def task_key(task_id: Union[UUID, str]) -> str:
    """
    Generate a Redis key for a task.
    
    Args:
        task_id: The task ID
        
    Returns:
        str: The Redis key
    """
    return KeyGenerator.generate_key("task", task_id)


def task_user_tasks_key(user_id: Union[UUID, str]) -> str:
    """
    Generate a Redis key for a user's task list.
    
    Args:
        user_id: The user ID
        
    Returns:
        str: The Redis key for the user's task list
    """
    return KeyGenerator.generate_key("user", user_id, "tasks")


def task_pattern(task_id: Union[UUID, str] = "*") -> str:
    """
    Generate a Redis key pattern for task keys.
    
    Args:
        task_id: Optional task ID (defaults to '*' for all tasks)
        
    Returns:
        str: The Redis key pattern
    """
    return KeyGenerator.generate_pattern("task", task_id)


def task_user_tasks_pattern(user_id: Union[UUID, str] = "*") -> str:
    """
    Generate a Redis key pattern for a user's task list.
    
    Args:
        user_id: Optional user ID (defaults to '*' for all users)
        
    Returns:
        str: The Redis key pattern for user task lists
    """
    return KeyGenerator.generate_pattern("user", user_id, "tasks")
