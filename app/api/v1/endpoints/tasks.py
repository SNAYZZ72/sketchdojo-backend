# =============================================================================
# app/api/v1/endpoints/tasks.py
# =============================================================================
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.domain.models.task import TaskStatus, TaskType
from app.domain.services.task_service import TaskService
from app.infrastructure.database.repositories.task_repository import TaskRepository
from app.schemas.task import PaginatedResponse, TaskListResponse, TaskResponse
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def get_user_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    status: Optional[TaskStatus] = Query(None),
    task_type: Optional[TaskType] = Query(None),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's tasks with pagination and filtering."""
    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    tasks, total = await task_service.get_user_tasks_paginated(
        current_user.id, page, size, status, task_type
    )

    return PaginatedResponse(
        items=[TaskListResponse.model_validate(task) for task in tasks],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task."""
    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task = await task_service.get_task(task_id, current_user.id)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this task"
        )


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running task."""
    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task = await task_service.cancel_task(task_id, current_user.id)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this task"
        )


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed task."""
    task_repo = TaskRepository(db)
    task_service = TaskService(task_repo)

    try:
        task = await task_service.retry_task(task_id, current_user.id)
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to retry this task"
        )
