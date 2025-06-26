"""
Tests for task key generation utilities.
"""
import pytest
from uuid import UUID, uuid4

from app.infrastructure.utils.task_keys import (
    task_key,
    task_user_tasks_key,
    task_pattern,
    task_user_tasks_pattern
)


def test_task_key():
    """Test generating a task key."""
    task_id = uuid4()
    expected = f"task:{task_id}"
    assert task_key(task_id) == expected
    assert task_key(str(task_id)) == expected


def test_task_user_tasks_key():
    """Test generating a user's task list key."""
    user_id = uuid4()
    expected = f"user:{user_id}:tasks"
    assert task_user_tasks_key(user_id) == expected
    assert task_user_tasks_key(str(user_id)) == expected


def test_task_pattern():
    """Test generating a task key pattern."""
    task_id = uuid4()
    
    # Test with specific task ID
    expected_specific = f"task:{task_id}"
    assert task_pattern(task_id) == expected_specific
    assert task_pattern(str(task_id)) == expected_specific
    
    # Test with wildcard
    assert task_pattern() == "task:*"


def test_task_user_tasks_pattern():
    """Test generating a user's task list key pattern."""
    user_id = uuid4()
    
    # Test with specific user ID
    expected_specific = f"user:{user_id}:tasks"
    assert task_user_tasks_pattern(user_id) == expected_specific
    assert task_user_tasks_pattern(str(user_id)) == expected_specific
    
    # Test with wildcard
    assert task_user_tasks_pattern() == "user:*:tasks"
