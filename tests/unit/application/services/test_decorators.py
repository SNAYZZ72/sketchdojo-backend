"""
Tests for service decorators.
"""
import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import BaseModel, Field

from app.application.services.decorators import (
    log_execution,
    validate_arguments,
    retry,
    transaction
)
from app.core.error_handling.base_error_handler import BaseErrorHandler
from app.core.error_handling.errors import ValidationError as AppValidationError


class TestLogExecution:
    """Tests for the log_execution decorator."""
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock(spec=logging.Logger)
    
    def test_log_execution_sync(self, mock_logger):
        """Test log_execution with a synchronous method."""
        # Given
        class TestService:
            logger = mock_logger
            
            @log_execution()
            def add(self, a: int, b: int) -> int:
                return a + b
        
        service = TestService()
        
        # When
        result = service.add(2, 3)
        
        # Then
        assert result == 5
        # Check that the log messages were called with the expected format
        mock_logger.log.assert_any_call(
            logging.DEBUG,
            "add called with args=(2, 3), kwargs={}",
            extra={}
        )
        mock_logger.log.assert_any_call(
            logging.DEBUG,
            "add completed successfully"
        )
    
    @pytest.mark.asyncio
    async def test_log_execution_async(self, mock_logger):
        """Test log_execution with an asynchronous method."""
        # Given
        class TestService:
            logger = mock_logger
            
            @log_execution()
            async def add(self, a: int, b: int) -> int:
                return a + b
        
        service = TestService()
        
        # When
        result = await service.add(2, 3)
        
        # Then
        assert result == 5
        # Check that the log messages were called with the expected format
        mock_logger.log.assert_any_call(
            logging.DEBUG,
            "add called with args=(2, 3), kwargs={}",
            extra={}
        )
        mock_logger.log.assert_any_call(
            logging.DEBUG,
            "add completed successfully"
        )
    
    def test_log_execution_with_exception(self, mock_logger):
        """Test log_execution when the method raises an exception."""
        # Given
        class TestService:
            logger = mock_logger
            
            @log_execution()
            def fail(self):
                raise ValueError("Test error")
        
        service = TestService()
        
        # When/Then
        with pytest.raises(ValueError, match="Test error"):
            service.fail()
        
        # Check that error was logged with the correct message format
        mock_logger.log.assert_any_call(
            logging.DEBUG,
            "fail called with args=(), kwargs={}",
            extra={}
        )
        # Check that error was logged with the correct message format
        mock_logger.error.assert_called_once_with(
            "fail failed with error: Test error",
            exc_info=True
        )


class TestValidateArguments:
    """Tests for the validate_arguments decorator."""
    
    class InputModel(BaseModel):
        """Test input model."""
        name: str
        age: int = Field(gt=0)
    
    class OutputModel(BaseModel):
        """Test output model."""
        message: str
        timestamp: datetime
    
    @pytest.fixture
    def mock_error_handler(self):
        """Create a mock error handler."""
        handler = MagicMock(spec=BaseErrorHandler)
        handler.handle_error = MagicMock()
        return handler
    
    def test_validate_arguments_success(self):
        """Test successful validation of arguments and return value."""
        # Given
        class TestService:
            @validate_arguments(input_model=TestValidateArguments.InputModel)
            def greet(self, name: str, age: int = 25) -> dict:
                return {"message": f"Hello, {name}!", "timestamp": datetime(2023, 1, 1)}
        
        service = TestService()
        
        # When
        result = service.greet("Alice", 30)
        
        # Then
        assert result == {"message": "Hello, Alice!", "timestamp": datetime(2023, 1, 1)}
    
    def test_validate_arguments_input_validation_error(self, mock_error_handler):
        """Test validation error for input arguments."""
        # Given
        class TestService:
            error_handler = mock_error_handler
            
            @validate_arguments(
                input_model=TestValidateArguments.InputModel,
                error_handler=error_handler
            )
            def greet(self, name: str, age: int = -1) -> dict:
                return {"message": f"Hello, {name}!", "timestamp": datetime(2023, 1, 1)}
        
        service = TestService()
        
        # When/Then
        with pytest.raises(AppValidationError):
            service.greet("Alice", -1)
        
        # Verify error handler was called
        mock_error_handler.handle_error.assert_called_once()
        error_arg = mock_error_handler.handle_error.call_args[0][0]
        assert isinstance(error_arg, AppValidationError)
        assert "Input should be greater than 0" in str(error_arg)
    
    @pytest.mark.asyncio
    async def test_validate_arguments_async(self):
        """Test validation with an async method."""
        # Given
        class TestService:
            @validate_arguments(
                input_model=TestValidateArguments.InputModel,
                output_model=TestValidateArguments.OutputModel
            )
            async def greet(self, name: str, age: int = 25) -> dict:
                return {"message": f"Hello, {name}!", "timestamp": datetime(2023, 1, 1)}
        
        service = TestService()
        
        # When
        result = await service.greet("Alice", 30)
        
        # Then
        assert result.message == "Hello, Alice!"
        assert result.timestamp == datetime(2023, 1, 1)


class TestRetry:
    """Tests for the retry decorator."""
    
    def test_retry_success_on_first_attempt(self, caplog):
        """Test retry when the first attempt succeeds."""
        # Given
        class TestService:
            attempts = 0
            
            @retry(max_attempts=3, exceptions=(ValueError,))
            def do_something(self):
                self.attempts += 1
                return "success"
        
        service = TestService()
        
        # When
        with caplog.at_level(logging.WARNING):
            result = service.do_something()
        
        # Then
        assert result == "success"
        assert service.attempts == 1
        assert len(caplog.records) == 0  # No retry logs
    
    def test_retry_success_after_retries(self, caplog, mocker):
        """Test retry when a later attempt succeeds."""
        # Given
        mock_sleep = mocker.patch('time.sleep')
        mock_logger = MagicMock()
        
        class TestService:
            attempts = 0
            logger = mock_logger
            
            @retry(max_attempts=3, exceptions=(ValueError,), backoff_factor=0.01)
            def do_something(self):
                self.attempts += 1
                if self.attempts < 2:
                    raise ValueError("Temporary failure")
                return "success"
        
        service = TestService()
        
        # When
        with caplog.at_level(logging.WARNING):
            result = service.do_something()
        
        # Then
        assert result == "success"
        assert service.attempts == 2
        # Verify sleep was called once with a positive delay
        mock_sleep.assert_called_once()
        assert mock_sleep.call_args[0][0] > 0
        # Check that the warning was logged
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "failed with Temporary failure" in warning_msg
        assert "retrying in" in warning_msg
        assert "attempt 1/3" in warning_msg
    
    def test_retry_all_attempts_fail(self, caplog, mocker):
        """Test retry when all attempts fail."""
        # Given
        mock_sleep = mocker.patch('time.sleep')
        mock_logger = MagicMock()
        
        class TestService:
            attempts = 0
            logger = mock_logger
            
            @retry(max_attempts=3, exceptions=(ValueError,), backoff_factor=0.01)
            def do_something(self):
                self.attempts += 1
                raise ValueError("Permanent failure")
        
        service = TestService()
        
        # When/Then
        with caplog.at_level(logging.WARNING), \
             pytest.raises(ValueError, match="Permanent failure"):
            service.do_something()
        
        # Then
        assert service.attempts == 3
        # Verify sleep was called twice (for 2 retries)
        assert mock_sleep.call_count == 2
        # Check that we have two retry log messages (for attempts 1 and 2)
        assert mock_logger.warning.call_count == 2
        # Verify the warning messages contain the expected content
        warning_msgs = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("attempt 1/3" in msg for msg in warning_msgs)
        assert any("attempt 2/3" in msg for msg in warning_msgs)
        assert all("Permanent failure" in msg for msg in warning_msgs)


class TestTransaction:
    """Tests for the transaction decorator."""
    
    class MockDB:
        """Mock database class for testing transactions."""
        
        def __init__(self):
            self.transaction = None
            self.committed = False
            self.rolled_back = False
            self._in_transaction = False
            
        def begin(self):
            if self._in_transaction:
                raise RuntimeError("Already in transaction")
            self._in_transaction = True
            self.transaction = self.MockTransaction(self)
            return self.transaction
            
        class MockTransaction:
            """Mock transaction class."""
            
            def __init__(self, db):
                self.db = db
                self.committed = False
                self.rolled_back = False
                
            def commit(self):
                if self.committed or self.rolled_back:
                    raise RuntimeError("Transaction already closed")
                self.committed = True
                self.db.committed = True
                self.db._in_transaction = False
                
            def rollback(self):
                if self.committed or self.rolled_back:
                    raise RuntimeError("Transaction already closed")
                self.rolled_back = True
                self.db.rolled_back = True
                self.db._in_transaction = False
                
            def __enter__(self):
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    if not self.rolled_back and not self.committed:
                        self.rollback()
                elif not self.committed and not self.rolled_back:
                    self.commit()
                return False
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    if not self.rolled_back and not self.committed:
                        self.rollback()
                elif not self.committed and not self.rolled_back:
                    self.commit()
                return False
                
    def test_transaction_sync_success(self):
        """Test successful synchronous transaction."""
        # Given
        db = self.MockDB()
        
        class TestService:
            def __init__(self):
                self.db = db
            
            @transaction()
            def do_something(self):
                return "success"
        
        service = TestService()
        
        # When
        result = service.do_something()
        
        # Then
        assert result == "success"
        assert db.committed
        assert not db.rolled_back
        assert not hasattr(db, 'transaction') or not db._in_transaction
    
    def test_transaction_sync_error(self):
        """Test synchronous transaction with error."""
        # Given
        db = self.MockDB()
        
        class TestService:
            def __init__(self):
                self.db = db
            
            @transaction(propagate_errors=True)
            def do_something(self):
                raise ValueError("Test error")
        
        service = TestService()
        
        # When/Then
        with pytest.raises(ValueError, match="Test error"):
            service.do_something()
        
        # Then
        assert not db.committed
        assert db.rolled_back
    
    @pytest.mark.asyncio
    async def test_transaction_async_success(self):
        """Test successful asynchronous transaction."""
        # Given
        db = self.MockDB()
        
        class TestService:
            def __init__(self):
                self.db = db
            
            @transaction()
            async def do_something(self):
                return "success"
        
        service = TestService()
        
        # When
        result = await service.do_something()
        
        # Then
        assert result == "success"
        assert db.committed
        assert not db.rolled_back
        assert not hasattr(db, 'transaction') or not db._in_transaction
    
    @pytest.mark.asyncio
    async def test_transaction_async_error(self):
        """Test asynchronous transaction with error."""
        # Given
        db = self.MockDB()
        
        class TestService:
            def __init__(self):
                self.db = db
            
            @transaction(propagate_errors=True)
            async def do_something(self):
                raise ValueError("Test error")
        
        service = TestService()
        
        # When/Then
        with pytest.raises(ValueError, match="Test error"):
            await service.do_something()
        
        # Then
        assert not db.committed
        assert db.rolled_back
        assert not hasattr(db, 'transaction') or not db._in_transaction
