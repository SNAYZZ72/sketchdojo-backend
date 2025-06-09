# app/tasks/celery_app.py
"""
Celery application configuration
"""
import logging
import os

from celery import Celery
from celery.signals import setup_logging, task_postrun, worker_ready

from app.config import get_settings

# Configure root logger to see all debug messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Get Redis URLs from environment variables with fallbacks to settings
redis_broker_url = os.environ.get('CELERY_BROKER_URL', os.environ.get('REDIS_URL', settings.celery_broker_url))
redis_result_backend = os.environ.get('CELERY_RESULT_BACKEND', os.environ.get('REDIS_URL', settings.celery_result_backend))

logger.debug(f"Celery broker URL: {redis_broker_url}")
logger.debug(f"Celery result backend: {redis_result_backend}")

# Create Celery app with explicit broker and backend URLs
celery_app = Celery(
    "sketchdojo",
    broker=redis_broker_url,
    backend=redis_result_backend,
)

# Explicitly configure task imports
celery_app.conf.imports = [
    "app.tasks.generation_tasks",
    "app.tasks.image_tasks",
    "app.tasks.notification_tasks",
]

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)


# Configure logging
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )
