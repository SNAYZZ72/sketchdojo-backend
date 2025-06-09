# app/tasks/test_tasks.py
"""
Simple test tasks to verify Celery configuration
"""
import logging
import time
import os
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def debug_task(self):
    """Test task that logs information and sleeps briefly"""
    task_id = self.request.id
    logger.debug(f"TEST TASK STARTED - Task ID: {task_id}")
    logger.debug(f"Environment: REDIS_URL={os.environ.get('REDIS_URL')}, CELERY_BROKER_URL={os.environ.get('CELERY_BROKER_URL')}")
    
    # Simulate work with a 5-second sleep
    logger.debug("Sleeping for 5 seconds...")
    time.sleep(5)
    
    logger.debug("TEST TASK COMPLETED")
    return {"status": "success", "message": f"Test task completed - {task_id}"}
