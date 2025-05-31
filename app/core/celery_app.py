# =============================================================================
# app/core/celery_app.py
# =============================================================================
import logging

from celery import Celery
from celery.signals import worker_init, worker_process_init
from kombu import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "sketchdojo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.webtoon_tasks",
        "app.tasks.image_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.cleanup_tasks",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
)

# Define task routes and queues
celery_app.conf.task_routes = {
    "app.tasks.ai_tasks.*": {"queue": "ai_processing"},
    "app.tasks.image_tasks.*": {"queue": "image_generation"},
    "app.tasks.webtoon_tasks.*": {"queue": "webtoon_processing"},
    "app.tasks.cleanup_tasks.*": {"queue": "maintenance"},
}

celery_app.conf.task_queues = (
    Queue("ai_processing", routing_key="ai_processing"),
    Queue("image_generation", routing_key="image_generation"),
    Queue("webtoon_processing", routing_key="webtoon_processing"),
    Queue("maintenance", routing_key="maintenance"),
)

# Configure retry policy
celery_app.conf.task_annotations = {
    "*": {
        "rate_limit": "100/m",
        "time_limit": 1800,  # 30 minutes
        "soft_time_limit": 1500,  # 25 minutes
    },
    "app.tasks.ai_tasks.generate_story_outline": {
        "rate_limit": "10/m",
        "priority": 8,
    },
    "app.tasks.image_tasks.generate_panel_image": {
        "rate_limit": "20/m",
        "priority": 7,
    },
}


@worker_init.connect
def worker_init_handler(sender=None, conf=None, **kwargs):
    """Initialize worker."""
    logger.info("Celery worker initialized")


@worker_process_init.connect
def worker_process_init_handler(sender=None, **kwargs):
    """Initialize worker process."""
    logger.info("Celery worker process initialized")
