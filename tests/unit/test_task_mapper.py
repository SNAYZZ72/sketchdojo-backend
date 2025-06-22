# tests/unit/test_task_mapper.py
"""
Tests for TaskDataMapper
"""
import uuid
from datetime import datetime

import pytest
from uuid import UUID

from app.domain.entities.generation_task import (
    GenerationTask,
    TaskProgress,
    TaskStatus,
    TaskType,
)
from app.domain.mappers.task_mapper import TaskDataMapper


class TestTaskDataMapper:
    """Test TaskDataMapper functionality"""

    def setup_method(self):
        """Initialize test data and mapper"""
        self.mapper = TaskDataMapper()
        self.task_id = uuid.uuid4()
        
        # Create a sample task
        progress = TaskProgress(
            current_step=2,
            total_steps=5,
            current_operation="Processing scene data",
            percentage=40,
        )
        
        self.task = GenerationTask(
            id=self.task_id,
            task_type=TaskType.STORY_GENERATION,
            status=TaskStatus.PROCESSING,
            progress=progress,
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=None,
            error_message=None,
            result={"partial_data": "Some partial results"},
            input_data={"title": "Test Story", "theme": "adventure"},
            metadata={"user_id": "user123", "priority": "high"},
        )

    def test_to_dict(self):
        """Test conversion of GenerationTask to dict"""
        # Convert to dict
        task_dict = self.mapper.to_dict(self.task)
        
        # Validate top-level properties
        assert task_dict["id"] == str(self.task_id)
        assert task_dict["task_type"] == TaskType.STORY_GENERATION.value
        assert task_dict["status"] == TaskStatus.PROCESSING.value
        assert task_dict["error_message"] is None
        
        # Validate progress
        assert isinstance(task_dict["progress"], dict)
        assert task_dict["progress"]["current_step"] == 2
        assert task_dict["progress"]["total_steps"] == 5
        assert task_dict["progress"]["current_operation"] == "Processing scene data"
        assert task_dict["progress"]["percentage"] == 40
        
        # Validate nested data
        assert task_dict["result"] == {"partial_data": "Some partial results"}
        assert task_dict["input_data"] == {"title": "Test Story", "theme": "adventure"}
        assert task_dict["metadata"] == {"user_id": "user123", "priority": "high"}

    def test_from_dict(self):
        """Test conversion from dict to GenerationTask"""
        # First convert to dict
        task_dict = self.mapper.to_dict(self.task)
        
        # Then convert back to object
        task = self.mapper.from_dict(task_dict)
        
        # Validate object
        assert isinstance(task, GenerationTask)
        assert task.id == self.task_id
        assert task.task_type == TaskType.STORY_GENERATION
        assert task.status == TaskStatus.PROCESSING
        assert task.error_message is None
        
        # Validate progress
        assert isinstance(task.progress, TaskProgress)
        assert task.progress.current_step == 2
        assert task.progress.total_steps == 5
        assert task.progress.current_operation == "Processing scene data"
        assert task.progress.percentage == 40
        
        # Validate nested data
        assert task.result == {"partial_data": "Some partial results"}
        assert task.input_data == {"title": "Test Story", "theme": "adventure"}
        assert task.metadata == {"user_id": "user123", "priority": "high"}
        
    def test_round_trip_conversion(self):
        """Test that converting to dict and back preserves all properties"""
        # Convert to dict and back
        task_dict = self.mapper.to_dict(self.task)
        task_new = self.mapper.from_dict(task_dict)
        
        # Test equality of key properties
        assert task_new.id == self.task.id
        assert task_new.task_type == self.task.task_type
        assert task_new.status == self.task.status
        
        # Test progress details
        assert task_new.progress.current_step == self.task.progress.current_step
        assert task_new.progress.total_steps == self.task.progress.total_steps
        assert task_new.progress.percentage == self.task.progress.percentage
        
        # Test data fields
        assert task_new.result == self.task.result
        assert task_new.input_data == self.task.input_data
        assert task_new.metadata == self.task.metadata
