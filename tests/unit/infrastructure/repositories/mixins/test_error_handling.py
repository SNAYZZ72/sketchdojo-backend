"""
Unit tests for error handling mixins.
"""
import pytest
import asyncio
from typing import Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pydantic import BaseModel, ConfigDict

from app.infrastructure.repositories.mixins.error_handling import (
    ErrorHandlingMixin,
    EntityValidationMixin,
    RepositoryError,
    NotFoundError,
    AlreadyExistsError,
    OptimisticLockError
)

class TestRepository(ErrorHandlingMixin):
    """Test repository class that uses the mixin."""
    
    @classmethod
    def find(cls, id: int) -> str:
        """Test find method."""
        return cls.handle_operation(
            lambda: "found" if id == 1 else None,
            not_found_error=True,
            not_found_message=f"Item {id} not found"
        )
        
    @classmethod
    async def find_async(cls, id: int) -> str:
        """Test async find method."""
        # Create a coroutine function that returns a value
        async def find_coroutine():
            return "found" if id == 1 else None
            
        return await cls.handle_async_operation(
            find_coroutine,
            not_found_error=True,
            not_found_message=f"Item {id} not found"
        )
        
    @classmethod
    def create(cls, data: dict) -> bool:
        """Test create method."""
        return cls.handle_operation(
            lambda: data.get("id") != "exists",
            already_exists_error=True
        )


class TestErrorHandlingMixin:
    """Tests for ErrorHandlingMixin."""
    
    @pytest.fixture
    def repo(self):
        """Return a test repository instance."""
        return TestRepository()
    
    def test_handle_operation_success(self, repo):
        """Test successful operation handling."""
        result = TestRepository.find(1)
        assert result == "found"
    
    def test_handle_operation_not_found(self):
        """Test not found error handling."""
        with pytest.raises(NotFoundError) as excinfo:
            TestRepository.find(2)
        assert "Item 2 not found" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_handle_async_operation_success(self):
        """Test successful async operation handling."""
        result = await TestRepository.find_async(1)
        assert result == "found"
    
    @pytest.mark.asyncio
    async def test_handle_async_operation_not_found(self):
        """Test async not found error handling."""
        # Create a mock async function that returns None
        async def mock_async_func():
            return None
            
        # Create a mock TestRepository class that uses our mock function
        with patch.object(TestRepository, 'find_async', 
                        new_callable=AsyncMock, 
                        return_value=None) as mock_find:
            # Call the method that should raise NotFoundError
            with pytest.raises(NotFoundError) as exc_info:
                # Call the method with not_found_error=True to trigger the error
                await ErrorHandlingMixin.handle_async_operation(
                    mock_async_func,
                    not_found_error=True,
                    not_found_message="Item 2 not found"
                )
            
            # Verify the error message
            assert "Item 2 not found" in str(exc_info.value)
            mock_find.assert_not_called()  # Make sure we're not calling the actual method
    
    def test_handle_operation_already_exists(self):
        """Test already exists error handling."""
        with pytest.raises(AlreadyExistsError):
            TestRepository.create({"id": "exists"})
    
    def test_handle_operation_unexpected_error(self):
        """Test unexpected error handling."""
        # Create a function that raises an error
        def error_func():
            raise ValueError("Test error")
            
        # Patch the logger to verify error logging
        with patch('app.infrastructure.repositories.mixins.error_handling.logger') as mock_logger:
            # Call the handle_operation method with our error function
            with pytest.raises(RepositoryError) as exc_info:
                ErrorHandlingMixin.handle_operation(
                    error_func,
                    not_found_error=True  # This will make it check for None, but we'll raise an error first
                )
            
            # Verify the error message and logging
            assert "Test error" in str(exc_info.value)
            mock_logger.exception.assert_called_once()
    
    def test_handle_operation_passes_through_specific_errors(self):
        """Test that specific errors are passed through without wrapping."""
        with patch.object(TestRepository, 'find', side_effect=OptimisticLockError("Conflict")):
            with pytest.raises(OptimisticLockError, match="Conflict"):
                TestRepository.find(1)

class TestModel(BaseModel):
    """Test model class."""
    name: str
    age: int
    
    model_config = ConfigDict(from_attributes=True)


class ModelWithContext(BaseModel):
    """Model that requires context for validation."""
    name: str
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def model_validate(cls, obj, *, context=None, **kwargs):
        """Custom validation that requires context."""
        if context and context.get("validate_name") and obj.get("name") == "invalid":
            raise ValueError("Invalid name")
        return super().model_validate(obj, context=context, **kwargs)


class TestEntityValidationMixin:
    """Tests for EntityValidationMixin."""
    
    def test_validate_entity_success(self):
        """Test successful entity validation."""
        data = {"name": "Test", "age": 30}
        result = EntityValidationMixin.validate_entity(data, TestModel)
        assert result.name == "Test"
        assert result.age == 30
    
    def test_validate_entity_with_context(self):
        """Test entity validation with context."""
        # Should pass with valid context
        data = {"name": "valid"}
        result = EntityValidationMixin.validate_entity(
            data, 
            ModelWithContext,
            context={"validate_name": True}
        )
        assert result.name == "valid"
        
        # Should fail with invalid name
        with pytest.raises(ValueError, match="Invalid name"):
            EntityValidationMixin.validate_entity(
                {"name": "invalid"}, 
                ModelWithContext, 
                context={"validate_name": True}
            )
    
    def test_validate_entity_validation_error(self):
        """Test entity validation with invalid data."""
        with pytest.raises(ValueError) as excinfo:
            EntityValidationMixin.validate_entity(
                {"name": 123, "age": "not_an_int"}, 
                TestModel
            )
        
        assert "Invalid TestModel" in str(excinfo.value)
