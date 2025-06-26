"""
Tests for the BaseErrorHandler class.
"""
import pytest
from typing import Any, Dict, Type
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.error_handling.base_error_handler import BaseErrorHandler


class TestError(Exception):
    """Test exception class."""
    pass


class TestErrorWithDetails(TestError):
    """Test exception with details."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}
        self.code = "test_error"


class TestErrorHandler(BaseErrorHandler[TestError]):
    """Test implementation of BaseErrorHandler."""
    
    def __init__(self, **kwargs):
        super().__init__(default_error_type=TestError, **kwargs)
        self.sent_errors = []
    
    async def send_error(self, error_response: Dict[str, Any], context: Dict[str, Any] = None) -> None:
        """Mock implementation of send_error for testing."""
        self.sent_errors.append((error_response, context))


class TestBaseErrorHandler:
    """Tests for BaseErrorHandler functionality."""
    
    @pytest.fixture
    def handler(self) -> TestErrorHandler:
        """Create a test error handler instance."""
        return TestErrorHandler()
    
    @pytest.mark.asyncio
    async def test_handle_error_with_test_error(self, handler: TestErrorHandler):
        """Test handling a test error."""
        error = TestError("Test error")
        
        await handler.handle_error(error)
        
        assert len(handler.sent_errors) == 1
        error_response, context = handler.sent_errors[0]
        assert error_response["message"] == "Test error"
        assert "details" not in error_response
    
    @pytest.mark.asyncio
    async def test_handle_error_with_details(self, handler: TestErrorHandler):
        """Test handling an error with details."""
        error = TestErrorWithDetails("Detailed error", {"field": "value"})
        
        await handler.handle_error(error, include_details=True)
        
        assert len(handler.sent_errors) == 1
        error_response, _ = handler.sent_errors[0]
        assert error_response["message"] == "Detailed error"
        assert error_response["code"] == "test_error"
        assert error_response["details"] == {"field": "value"}
    
    @pytest.mark.asyncio
    async def test_handle_error_with_unexpected_error(self, handler: TestErrorHandler):
        """Test handling an unexpected error type."""
        error = ValueError("Unexpected error")
        
        await handler.handle_error(error)
        
        assert len(handler.sent_errors) == 1
        error_response, _ = handler.sent_errors[0]
        assert error_response["message"] == "An unexpected error occurred"
        assert error_response["code"] == "internal_error"
    
    @pytest.mark.asyncio
    async def test_wrap_async_handler_success(self, handler: TestErrorHandler):
        """Test wrapping an async handler that succeeds."""
        mock_handler = AsyncMock(return_value="success")
        
        wrapped = handler.wrap_async_handler(mock_handler)
        result = await wrapped("arg1", key="value")
        
        assert result == "success"
        mock_handler.assert_awaited_once_with("arg1", key="value")
        assert len(handler.sent_errors) == 0
    
    @pytest.mark.asyncio
    async def test_wrap_async_handler_error(self, handler: TestErrorHandler):
        """Test wrapping an async handler that raises an error."""
        error = TestError("Handler error")
        mock_handler = AsyncMock(side_effect=error)
        
        wrapped = handler.wrap_async_handler(mock_handler)
        result = await wrapped("arg1", key="value")
        
        assert result is None
        mock_handler.assert_awaited_once_with("arg1", key="value")
        assert len(handler.sent_errors) == 1
        error_response, _ = handler.sent_errors[0]
        assert error_response["message"] == "Handler error"
    
    def test_decorator_syntax(self, handler: TestErrorHandler):
        """Test using the handler as a decorator."""
        @handler()
        async def test_func():
            return "success"
            
        assert test_func is not None
