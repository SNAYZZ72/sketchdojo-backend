# app/api/v1/routes/test.py
"""
Test API routes for debugging and monitoring
"""
import logging
from fastapi import APIRouter, HTTPException

from app.tasks.celery_app import celery_app
from app.tasks.test_tasks import debug_task

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/celery-test")
async def test_celery():
    """Simple endpoint to test Celery task execution"""
    try:
        logger.debug("Submitting test task to Celery")
        task = debug_task.delay()
        
        return {
            "status": "success",
            "message": "Test task submitted to Celery",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Error submitting test task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/celery-task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a submitted Celery task"""
    try:
        task = celery_app.AsyncResult(task_id)
        
        result = {
            "task_id": task_id,
            "status": task.status,
        }
        
        # Include result if task is complete
        if task.ready():
            if task.successful():
                result["result"] = task.result
            else:
                result["error"] = str(task.result)
        
        return result
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
