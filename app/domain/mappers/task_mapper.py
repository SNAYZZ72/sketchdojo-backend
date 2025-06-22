# app/domain/mappers/task_mapper.py
"""
Data mapper for GenerationTask entities
"""
from datetime import datetime
from uuid import UUID

from app.domain.entities.generation_task import (
    GenerationTask,
    TaskProgress,
    TaskStatus,
    TaskType,
)


class TaskDataMapper:
    """Mapper for converting between GenerationTask entities and dict representations"""

    def to_dict(self, task: GenerationTask) -> dict:
        """
        Convert a GenerationTask entity to a dictionary representation
        
        Args:
            task: The task entity to convert
            
        Returns:
            Dictionary representation of the task
        """
        return {
            "id": str(task.id),
            "task_type": task.task_type.value,
            "status": task.status.value,
            "progress": {
                "current_step": task.progress.current_step,
                "total_steps": task.progress.total_steps,
                "current_operation": task.progress.current_operation,
                "percentage": task.progress.percentage,
            },
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "result": task.result,
            "input_data": task.input_data,
            "metadata": task.metadata,
        }

    def from_dict(self, data: dict) -> GenerationTask:
        """
        Convert a dictionary to a GenerationTask entity
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            GenerationTask entity
        """
        progress = TaskProgress(
            current_step=data["progress"]["current_step"],
            total_steps=data["progress"]["total_steps"],
            current_operation=data["progress"]["current_operation"],
            percentage=data["progress"]["percentage"],
        )

        task = GenerationTask(
            id=UUID(data["id"]),
            task_type=TaskType(data["task_type"]),
            status=TaskStatus(data["status"]),
            progress=progress,
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            error_message=data["error_message"],
            result=data["result"],
            input_data=data.get("input_data", {}),
            metadata=data.get("metadata", {}),
        )

        return task
