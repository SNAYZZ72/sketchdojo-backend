# app/api/v1/routes/tasks.py
"""
Task management API routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_task_repository
from app.domain.entities.generation_task import TaskStatus, TaskType
from app.domain.repositories.task_repository import TaskRepository
from app.schemas.task_schemas import TaskListResponse, TaskResponse

router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: UUID, repository: TaskRepository = Depends(get_task_repository)
):
    """Get task status by ID"""
    task = await repository.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse.from_entity(task)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: TaskStatus = Query(None, description="Filter by status"),
    task_type: TaskType = Query(None, description="Filter by type"),
    repository: TaskRepository = Depends(get_task_repository),
):
    """List tasks with optional filters"""
    try:
        if status:
            tasks = await repository.get_by_status(status)
        elif task_type:
            tasks = await repository.get_by_type(task_type)
        else:
            tasks = await repository.get_all()

        return TaskListResponse(
            tasks=[TaskResponse.from_entity(t) for t in tasks],
            total=len(tasks),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def cancel_task(
    task_id: UUID, repository: TaskRepository = Depends(get_task_repository)
):
    """Cancel a task"""
    task = await repository.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.is_terminal:
        raise HTTPException(status_code=400, detail="Task is already completed")

    task.cancel()
    await repository.save(task)

    return {"message": "Task cancelled successfully"}
