"""
Decorators for repository operations.

This module provides decorators that can be used to add common functionality
to repository methods, such as transaction management, retry logic, and logging.
"""
import functools
import inspect
import logging
import time
from typing import Any, Callable, Optional, Type, TypeVar, cast

from pydantic import BaseModel

from app.infrastructure.repositories.mixins.error_handling import (
    RepositoryError,
    NotFoundError,
    AlreadyExistsError,
    OptimisticLockError,
)

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

logger = logging.getLogger(__name__)


def transaction(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle database transactions.
    
    This decorator ensures that the wrapped function is executed within a transaction.
    If the function completes successfully, the transaction is committed. If an exception
    is raised, the transaction is rolled back.
    
    Args:
        fn: The function to wrap with transaction handling
        
    Returns:
        The wrapped function with transaction handling
    """
    @functools.wraps(fn)
    def wrapper(self, *args: Any, **kwargs: Any) -> T:
        # Check if we're already in a transaction
        in_transaction = getattr(self, '_in_transaction', False)
        
        # If already in a transaction, just execute the function
        if in_transaction:
            return fn(self, *args, **kwargs)
            
        # Otherwise, start a new transaction
        try:
            # Set the transaction flag
            self._in_transaction = True
            
            # Execute the function
            result = fn(self, *args, **kwargs)
            
            # If we have a commit method, call it
            if hasattr(self, 'commit'):
                self.commit()  # type: ignore
                
            return result
            
        except Exception as e:
            # Rollback on error if we have a rollback method
            if hasattr(self, 'rollback'):
                self.rollback()  # type: ignore
            raise
            
        finally:
            # Clear the transaction flag
            self._in_transaction = False
            
    return wrapper


def retry(
    max_retries: int = 3,
    retry_delay: float = 0.1,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add retry logic to a function.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry on
        backoff_factor: Factor to multiply delay by after each retry
        
    Returns:
        A decorator that adds retry logic to the wrapped function
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        # Get the function name for logging
        func_name = getattr(fn, '__name__', str(fn))
        
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            delay = retry_delay
            last_exception = None
            
            while retries <= max_retries:
                try:
                    return fn(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(
                            "Max retries (%d) reached for %s",
                            max_retries,
                            func_name,
                            exc_info=True
                        )
                        raise
                        
                    logger.warning(
                        "Retry %d/%d for %s after exception: %s",
                        retries,
                        max_retries,
                        func_name,
                        str(e)
                    )
                    
                    # Sleep before retrying
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # This should never be reached due to the raise in the except block
            raise RuntimeError("Unexpected error in retry logic")
                    
        return wrapper
    return decorator


def log_execution(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log method execution time and result/error.
    
    Args:
        fn: The function to wrap with logging
        
    Returns:
        The wrapped function with logging
    """
    # Get the function name for logging
    func_name = getattr(fn, '__name__', str(fn))
    
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Get instance info if this is a method
        instance = args[0] if args and hasattr(args[0], func_name) else None
        
        # Format args for logging (skip 'self' for instance methods)
        log_args = args[1:] if instance is not None else args
        
        # Log the start of execution
        logger.debug(
            "Executing %s with args=%s, kwargs=%s",
            func_name,
            log_args,
            kwargs
        )
        
        start_time = time.monotonic()
        
        try:
            result = fn(*args, **kwargs)
            
            # Log successful completion
            logger.debug(
                "%s completed in %.4f seconds",
                func_name,
                time.monotonic() - start_time
            )
            
            return result
            
        except Exception as e:
            # Log the error
            duration = time.monotonic() - start_time
            logger.error(
                "%s failed after %.4f seconds: %s",
                func_name,
                duration,
                str(e),
                exc_info=True
            )
            raise
            
    return wrapper


def validate_arguments(*validators: Callable[..., None]) -> Callable[..., Callable[..., T]]:
    """
    Decorator to validate function arguments.
    
    Each validator function should accept the argument value as its first parameter
    and optionally accept a parameter named 'field_name' to get the name of the
    argument being validated.
    
    Example:
        @validate_arguments(
            lambda x, field_name: x > 0 or _("{} must be positive".format(field_name))
        )
        def my_function(value: int) -> int:
            return value
    
    Args:
        *validators: One or more validator functions. Each validator should accept
                    the argument value as its first parameter and raise an exception
                    if the validation fails.
                    
    Returns:
        A decorator that validates function arguments
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        # Get the function signature for better error messages
        sig = inspect.signature(fn)
        
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Bind the arguments to the function signature
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Call each validator with each argument
            for param_name, param_value in bound_args.arguments.items():
                for validator in validators:
                    try:
                        # Call the validator with the parameter value
                        validator(param_value, field_name=param_name)
                    except Exception as e:
                        # Re-raise with a more descriptive error message
                        error_msg = str(e)
                        if not error_msg:
                            error_msg = f"Invalid value for {param_name}"
                        raise ValueError(f"Validation failed for {fn.__name__}: {error_msg}") from e
            
            return fn(*args, **kwargs)
            
        return wrapper
    return decorator


def cache_result(cache_key_fn: Optional[Callable[..., str]] = None) -> Callable[..., Callable[..., T]]:
    """
    Decorator to cache the result of a function.
    
    Args:
        cache_key_fn: Optional function to generate a cache key from function arguments.
                     If not provided, a default key based on function name and arguments is used.
                     
    Returns:
        A decorator that caches function results
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(self, *args: Any, **kwargs: Any) -> T:
            # Skip caching if no cache is available
            if not hasattr(self, '_cache'):
                return fn(self, *args, **kwargs)
                
            # Generate cache key
            if cache_key_fn:
                key = cache_key_fn(*args, **kwargs)
            else:
                # Default key format: function_name:arg1:arg2:...
                key_parts = [fn.__name__] + [str(arg) for arg in args[1:]]  # Skip 'self'
                key = ':'.join(key_parts)
                
            # Check cache
            cache = self._cache  # type: ignore
            if hasattr(cache, 'get') and hasattr(cache, 'set'):
                cached_result = cache.get(key)
                if cached_result is not None:
                    logger.debug("Cache hit for key: %s", key)
                    return cached_result
                    
            # Not in cache, call the function
            result = fn(self, *args, **kwargs)
            
            # Cache the result
            if hasattr(cache, 'set'):
                try:
                    cache.set(key, result)
                    logger.debug("Cached result for key: %s", key)
                except Exception as e:
                    logger.warning("Failed to cache result: %s", str(e))
                    
            return result
            
        return wrapper
    return decorator
