# app/tasks/__init__.py
"""
Celery background tasks
"""
# First import the Celery app
from app.tasks.celery_app import celery_app

# Import all task modules so they are registered with Celery
# Using relative imports to avoid circular dependencies
from . import test_tasks, generation_tasks, image_tasks, notification_tasks

# This ensures tasks are properly registered when Celery imports this package
__all__ = ['celery_app', 'test_tasks', 'generation_tasks', 'image_tasks', 'notification_tasks']
