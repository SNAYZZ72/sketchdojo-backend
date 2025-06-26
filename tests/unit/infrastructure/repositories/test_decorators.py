"""Unit tests for repository decorators."""
import asyncio
import time
from unittest.mock import MagicMock, patch, call
import pytest

from app.infrastructure.repositories.decorators import (
    transaction,
    retry,
    log_execution,
    validate_arguments,
    cache_result,
)

class TestTransactionDecorator:
    """Test the transaction decorator."""
    
    def test_transaction_commits_on_success(self):
        """Test that the transaction commits on successful execution."""
        # Create a mock class with commit and rollback methods
        class TestRepo:
            def __init__(self):
                self.committed = False
                self.rolled_back = False
                
            @transaction
            def do_something(self):
                return "success"
                
            def commit(self):
                self.committed = True
                
            def rollback(self):
                self.rolled_back = True
        
        # Test the decorated method
        repo = TestRepo()
        result = repo.do_something()
        
        assert result == "success"
        assert repo.committed is True
        assert repo.rolled_back is False
    
    def test_transaction_rolls_back_on_error(self):
        """Test that the transaction rolls back on error."""
        class TestRepo:
            def __init__(self):
                self.committed = False
                self.rolled_back = False
                
            @transaction
            def do_something(self):
                raise ValueError("Test error")
                
            def commit(self):
                self.committed = True
                
            def rollback(self):
                self.rolled_back = True
        
        # Test the decorated method
        repo = TestRepo()
        
        with pytest.raises(ValueError, match="Test error"):
            repo.do_something()
            
        assert repo.committed is False
        assert repo.rolled_back is True
    
    def test_nested_transactions(self):
        """Test that nested transactions don't create multiple commits."""
        class TestRepo:
            def __init__(self):
                self.commit_count = 0
                self.rollback_count = 0
                
            @transaction
            def outer_method(self):
                return self.inner_method()
                
            @transaction
            def inner_method(self):
                return "success"
                
            def commit(self):
                self.commit_count += 1
                
            def rollback(self):
                self.rollback_count += 1
        
        # Test the decorated method
        repo = TestRepo()
        result = repo.outer_method()
        
        assert result == "success"
        assert repo.commit_count == 1
        assert repo.rollback_count == 0


class TestRetryDecorator:
    """Test the retry decorator."""
    
    def test_retry_success_on_first_attempt(self):
        """Test that the function works on first attempt."""
        mock_func = MagicMock(return_value="success")
        
        decorated = retry(max_retries=3)(mock_func)
        result = decorated()
        
        assert result == "success"
        mock_func.assert_called_once()
    
    def test_retry_succeeds_after_retries(self):
        """Test that the function succeeds after some retries."""
        mock_func = MagicMock()
        mock_func.side_effect = [ValueError("Error 1"), ValueError("Error 2"), "success"]
        
        decorated = retry(max_retries=3, retry_delay=0.01)(mock_func)
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_retry_exhausts_attempts(self):
        """Test that the function gives up after max retries."""
        mock_func = MagicMock()
        mock_func.side_effect = ValueError("Test error")
        
        decorated = retry(max_retries=2, retry_delay=0.01)(mock_func)
        
        with pytest.raises(ValueError, match="Test error"):
            decorated()
            
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    def test_retry_only_on_specific_exceptions(self):
        """Test that only specified exceptions are retried."""
        mock_func = MagicMock()
        mock_func.side_effect = KeyError("Key error")
        
        # Only retry on ValueError, not KeyError
        decorated = retry(
            max_retries=2, 
            retry_delay=0.01, 
            exceptions=(ValueError,)
        )(mock_func)
        
        with pytest.raises(KeyError, match="Key error"):
            decorated()
            
        assert mock_func.call_count == 1  # No retries for KeyError


class TestLogExecutionDecorator:
    """Test the log_execution decorator."""
    
    @patch('app.infrastructure.repositories.decorators.logger')
    def test_log_execution_success(self, mock_logger):
        """Test logging of successful execution."""
        @log_execution
        def test_func(arg1, kwarg1=None):
            return f"success: {arg1} {kwarg1}"
        
        result = test_func("test", kwarg1="value")
        
        assert result == "success: test value"
        
        # Check debug logs were called at least twice (start and completion)
        assert mock_logger.debug.call_count >= 2
        
        # Get all debug call arguments
        debug_calls = mock_logger.debug.call_args_list
        
        # Check for execution start message
        start_calls = [call for call in debug_calls 
                      if len(call[0]) > 0 and call[0][0] == "Executing %s with args=%s, kwargs=%s"]
        assert len(start_calls) == 1
        
        # Check the start call arguments
        start_call = start_calls[0][0]
        assert len(start_call) == 4  # format string + 3 format args
        assert start_call[1] == "test_func"  # function name
        assert start_call[2] == ("test",)  # args
        assert start_call[3] == {"kwarg1": "value"}  # kwargs
        
        # Check for completion message
        complete_calls = [call for call in debug_calls 
                        if len(call[0]) > 0 and call[0][0] == "%s completed in %.4f seconds"]
        assert len(complete_calls) == 1
        
        # Check the completion call arguments
        complete_call = complete_calls[0][0]
        assert len(complete_call) == 3  # format string + 2 format args
        assert complete_call[1] == "test_func"  # function name
        assert isinstance(complete_call[2], float)  # duration
    
    @patch('app.infrastructure.repositories.decorators.logger')
    def test_log_execution_error(self, mock_logger):
        """Test logging of failed execution."""
        @log_execution
        def test_func():
            raise ValueError("Test error")
    
        with pytest.raises(ValueError, match="Test error"):
            test_func()
    
        # Check error log was called exactly once
        assert mock_logger.error.call_count == 1
        
        # Get the error call arguments
        error_call = mock_logger.error.call_args_list[0][0]
        
        # Check the error message format
        assert len(error_call) >= 4  # format string + 3 format args + exc_info
        assert error_call[0] == "%s failed after %.4f seconds: %s"  # format string
        assert error_call[1] == "test_func"  # function name
        assert isinstance(error_call[2], float)  # duration
        assert "Test error" in error_call[3]  # error message
        
        # Check exc_info was passed
        error_kwargs = mock_logger.error.call_args_list[0][1]
        assert error_kwargs.get("exc_info") is True
        assert "Test error" in str(error_call)


class TestValidateArgumentsDecorator:
    """Test the validate_arguments decorator."""
    
    def test_validate_arguments_success(self):
        """Test validation of valid arguments."""
        def validate_positive(x, field_name=None):
            if x <= 0:
                raise ValueError(f"{field_name} must be positive" if field_name else "Must be positive")
    
        @validate_arguments(validate_positive)
        def add(a, b):
            return a + b
    
        # Test with valid input
        assert add(1, 2) == 3
        
        # Test with keyword arguments
        assert add(a=1, b=2) == 3
    
    def test_validate_arguments_failure(self):
        """Test validation of invalid arguments."""
        def validate_positive(x, field_name=None):
            if x <= 0:
                raise ValueError(f"{field_name} must be positive" if field_name else "Must be positive")
        
        @validate_arguments(validate_positive)
        def add(a, b):
            return a + b
        
        # Test with invalid positional argument
        with pytest.raises(ValueError, match=r"Validation failed for add: a must be positive"):
            add(-1, 2)
            
        # Test with invalid keyword argument
        with pytest.raises(ValueError, match=r"Validation failed for add: a must be positive"):
            add(a=-1, b=2)
    
    def test_multiple_validators(self):
        """Test multiple validators."""
        def validate_positive(x, field_name=None):
            if x <= 0:
                raise ValueError(f"{field_name} must be positive" if field_name else "Must be positive")
                
        def validate_even(x, field_name=None):
            if x % 2 != 0:
                raise ValueError(f"{field_name} must be even" if field_name else "Must be even")
        
        @validate_arguments(validate_positive, validate_even)
        def process_number(x):
            return x * 2
        
        # Should pass with positional arguments
        assert process_number(2) == 4
        
        # Should pass with keyword arguments
        assert process_number(x=4) == 8
        
        # Should fail - not positive (positional)
        with pytest.raises(ValueError, match=r"Validation failed for process_number: x must be positive"):
            process_number(-2)
            
        # Should fail - not even (positional)
        with pytest.raises(ValueError, match=r"Validation failed for process_number: x must be even"):
            process_number(3)
            
        # Should fail - not positive (keyword)
        with pytest.raises(ValueError, match=r"Validation failed for process_number: x must be positive"):
            process_number(x=-4)
            
        # Should fail - not even (keyword)
        with pytest.raises(ValueError, match=r"Validation failed for process_number: x must be even"):
            process_number(x=5)


class TestCacheResultDecorator:
    """Test the cache_result decorator."""
    
    def test_cache_result(self):
        """Test that results are cached."""
        class TestCache:
            def __init__(self):
                self.cache = {}
                
            def get(self, key):
                return self.cache.get(key)
                
            def set(self, key, value):
                self.cache[key] = value
        
        class TestRepo:
            def __init__(self):
                self._cache = TestCache()
                self.call_count = 0
            
            @cache_result()
            def get_data(self, key):
                self.call_count += 1
                return f"data_for_{key}"
        
        # First call - should cache the result
        repo = TestRepo()
        result1 = repo.get_data("test")
        
        assert result1 == "data_for_test"
        assert repo.call_count == 1
        
        # Second call with same args - should use cache
        result2 = repo.get_data("test")
        
        assert result2 == "data_for_test"
        assert repo.call_count == 1  # Should not call the function again
    
    def test_cache_with_custom_key(self):
        """Test cache with custom key function."""
        class TestCache:
            def __init__(self):
                self.cache = {}
                
            def get(self, key):
                return self.cache.get(key)
                
            def set(self, key, value):
                self.cache[key] = value
        
        def custom_key(user_id, **kwargs):
            return f"user:{user_id}"
        
        class TestRepo:
            def __init__(self):
                self._cache = TestCache()
                self.call_count = 0
            
            @cache_result(cache_key_fn=custom_key)
            def get_user_data(self, user_id, include_details=False):
                self.call_count += 1
                return {"user_id": user_id, "details": include_details}
        
        # First call - should cache with custom key
        repo = TestRepo()
        result1 = repo.get_user_data(123, include_details=True)
        
        assert result1 == {"user_id": 123, "details": True}
        assert repo.call_count == 1
        
        # Second call with different kwargs but same user_id - should use cache
        result2 = repo.get_user_data(123, include_details=False)
        
        assert result2 == {"user_id": 123, "details": True}  # Cached result
        assert repo.call_count == 1  # Should not call the function again
    
    def test_cache_skipped_when_no_cache(self):
        """Test that caching is skipped when no cache is available."""
        class TestRepo:
            def __init__(self):
                self.call_count = 0
            
            @cache_result()
            def get_data(self, key):
                self.call_count += 1
                return f"data_for_{key}"
        
        # Should work even without _cache attribute
        repo = TestRepo()
        result1 = repo.get_data("test")
        result2 = repo.get_data("test")
        
        assert result1 == "data_for_test"
        assert result2 == "data_for_test"
        assert repo.call_count == 2  # Should call the function twice (no caching)
