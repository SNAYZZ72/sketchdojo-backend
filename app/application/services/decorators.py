"""
Decorators for service layer methods to handle cross-cutting concerns.
"""
import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel, ValidationError

from app.core.error_handling.base_error_handler import BaseErrorHandler
from app.core.error_handling.errors import ValidationError as AppValidationError

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def log_execution(logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
    """
    Decorator to log method entry, exit, and execution time.
    
    Args:
        logger: Optional logger instance. If not provided, uses the service's logger.
        level: Logging level to use (default: DEBUG)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Get the logger from the service if not provided
            log = logger or getattr(self, 'logger', None)
            if not log:
                return await func(self, *args, **kwargs)
            
            # Get parameter names and values
            sig = inspect.signature(func)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            
            # Log method entry
            log.log(level, f"{func.__name__} called with args={args}, kwargs={kwargs}",
                   extra=kwargs)
            
            try:
                # Call the original method
                result = await func(self, *args, **kwargs)
                
                # Log method exit
                log.log(level, f"{func.__name__} completed successfully")
                return result
                
            except Exception as e:
                # Log any exceptions
                log.error(f"{func.__name__} failed with error: {str(e)}", 
                        exc_info=True)
                raise
                
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Get the logger from the service if not provided
            log = logger or getattr(self, 'logger', None)
            if not log:
                return func(self, *args, **kwargs)
            
            # Log method entry
            log.log(level, f"{func.__name__} called with args={args}, kwargs={kwargs}",
                   extra=kwargs)
            
            try:
                # Call the original method
                result = func(self, *args, **kwargs)
                
                # Log method exit
                log.log(level, f"{func.__name__} completed successfully")
                return result
                
            except Exception as e:
                # Log any exceptions
                log.error(f"{func.__name__} failed with error: {str(e)}", 
                        exc_info=True)
                raise
                
        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
    
    return decorator


def validate_arguments(
    input_model: Optional[Type[BaseModel]] = None,
    output_model: Optional[Type[BaseModel]] = None,
    error_handler: Optional[BaseErrorHandler] = None
):
    """
    Decorator to validate method arguments and return values using Pydantic models.
    
    Args:
        input_model: Pydantic model for validating input arguments
        output_model: Pydantic model for validating return value
        error_handler: Optional error handler for validation errors
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Get the service's error handler if not provided
            handler = error_handler or getattr(self, 'error_handler', None)
            
            try:
                # Validate input if input_model is provided
                if input_model:
                    # Create a dictionary of named arguments
                    sig = inspect.signature(func)
                    bound_args = sig.bind(self, *args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Convert to dict and remove 'self'
                    input_data = dict(bound_args.arguments)
                    input_data.pop('self', None)
                    
                    # Validate using Pydantic model
                    validated_input = input_model.model_validate(input_data)
                    
                    # Replace original args/kwargs with validated data
                    if args:
                        # For positional arguments, we'd need to know which ones to replace
                        # This is a simplified version that works for kwargs only
                        pass
                    if kwargs:
                        kwargs.update(validated_input.model_dump())
                
                # Call the original method
                result = await func(self, *args, **kwargs)
                
                # Validate output if output_model is provided
                if output_model and result is not None:
                    if isinstance(result, tuple):
                        # For multiple return values, validate each one that matches the model
                        validated_results = []
                        for item in result:
                            if isinstance(item, dict):
                                validated_results.append(output_model.model_validate(item))
                            else:
                                validated_results.append(item)
                        return tuple(validated_results)
                    elif isinstance(result, dict):
                        return output_model.model_validate(result)
                    else:
                        return output_model.model_validate({"result": result}).result
                
                return result
                
            except ValidationError as e:
                # Handle validation errors
                if handler:
                    handler.handle_error(AppValidationError(str(e)), {
                        "function": func.__name__,
                        "input_model": input_model.__name__ if input_model else None,
                        "output_model": output_model.__name__ if output_model else None,
                        "error_details": e.errors()
                    })
                raise AppValidationError("Validation error: " + str(e)) from e
                
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Get the service's error handler if not provided
            handler = error_handler or getattr(self, 'error_handler', None)
            
            try:
                # Validate input if input_model is provided
                if input_model:
                    # Create a dictionary of named arguments
                    sig = inspect.signature(func)
                    bound_args = sig.bind(self, *args, **kwargs)
                    bound_args.apply_defaults()
                    
                    # Convert to dict and remove 'self'
                    input_data = dict(bound_args.arguments)
                    input_data.pop('self', None)
                    
                    # Validate using Pydantic model
                    validated_input = input_model.model_validate(input_data)
                    
                    # Replace original args/kwargs with validated data
                    if args:
                        # For positional arguments, we'd need to know which ones to replace
                        # This is a simplified version that works for kwargs only
                        pass
                    if kwargs:
                        kwargs.update(validated_input.model_dump())
                
                # Call the original method
                result = func(self, *args, **kwargs)
                
                # Validate output if output_model is provided
                if output_model and result is not None:
                    if isinstance(result, tuple):
                        # For multiple return values, validate each one that matches the model
                        validated_results = []
                        for item in result:
                            if isinstance(item, dict):
                                validated_results.append(output_model.model_validate(item))
                            else:
                                validated_results.append(item)
                        return tuple(validated_results)
                    elif isinstance(result, dict):
                        return output_model.model_validate(result)
                    else:
                        return output_model.model_validate({"result": result}).result
                
                return result
                
            except ValidationError as e:
                # Handle validation errors
                if handler:
                    handler.handle_error(AppValidationError(str(e)), {
                        "function": func.__name__,
                        "input_model": input_model.__name__ if input_model else None,
                        "output_model": output_model.__name__ if output_model else None,
                        "error_details": e.errors()
                    })
                raise AppValidationError("Validation error: " + str(e)) from e
        
        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
    
    return decorator


def retry(max_attempts: int = 3, 
          exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
          backoff_factor: float = 0.1):
    """
    Decorator to retry a function when exceptions occur.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        exceptions: Exception(s) to catch and retry on (default: Exception)
        backoff_factor: Factor to multiply the delay between retries (default: 0.1)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(self, *args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                        
                    # Calculate backoff time with jitter to avoid thundering herd
                    base_delay = backoff_factor * (2 ** (attempt - 1))
                    jitter = base_delay * 0.1  # Add 10% jitter
                    delay = base_delay + (jitter * (2 * (hash(str(id(self)) + str(attempt)) / (2**64 - 1)) - 1))
                    
                    # Log the retry
                    logger = getattr(self, 'logger', None)
                    if logger:
                        logger.warning(
                            f"{func.__name__} failed with {str(e)}, retrying in {delay:.2f} seconds (attempt {attempt}/{max_attempts})",
                            extra={"error": str(e), "attempt": attempt, "max_attempts": max_attempts, "delay": delay}
                        )
                    
                    # Wait before retrying
                    import asyncio
                    await asyncio.sleep(delay)
            
            # If we get here, all attempts failed
            if last_exception:
                raise last_exception
            
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(self, *args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                        
                    # Calculate backoff time with jitter to avoid thundering herd
                    base_delay = backoff_factor * (2 ** (attempt - 1))
                    jitter = base_delay * 0.1  # Add 10% jitter
                    delay = base_delay + (jitter * (2 * (hash(str(id(self)) + str(attempt)) / (2**64 - 1)) - 1))
                    
                    # Log the retry
                    logger = getattr(self, 'logger', None)
                    if logger:
                        logger.warning(
                            f"{func.__name__} failed with {str(e)}, retrying in {delay:.2f} seconds (attempt {attempt}/{max_attempts})",
                            extra={"error": str(e), "attempt": attempt, "max_attempts": max_attempts, "delay": delay}
                        )
                    
                    # Wait before retrying
                    import time
                    time.sleep(delay)
            
            # If we get here, all attempts failed
            if last_exception:
                raise last_exception
        
        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
    
    return decorator


def transaction(propagate_errors: bool = False):
    """
    Decorator to wrap a method in a transaction.
    
    Args:
        propagate_errors: If True, allows exceptions to propagate after rolling back
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Get the database session or connection from the service
            db = getattr(self, 'db', None) or getattr(self, 'session', None)
            
            if not db:
                # No database session found, just call the function
                return await func(self, *args, **kwargs)
            
            # Start a transaction
            async with db.begin():
                try:
                    result = await func(self, *args, **kwargs)
                    return result
                except Exception as e:
                    # Rollback on error
                    if hasattr(db, 'rollback'):
                        await db.rollback()
                    elif hasattr(db, 'rollback'):
                        db.rollback()
                    
                    # Log the error
                    logger = getattr(self, 'logger', None)
                    if logger:
                        logger.error("Transaction failed: %s", str(e), exc_info=True)
                    
                    if propagate_errors:
                        raise
                    
                    # Re-raise with additional context
                    raise RuntimeError(f"Transaction failed: {str(e)}") from e
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Get the database session or connection from the service
            db = getattr(self, 'db', None) or getattr(self, 'session', None)
            
            if not db:
                # No database session found, just call the function
                return func(self, *args, **kwargs)
            
            # Start a transaction
            with db.begin():
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as e:
                    # Rollback on error
                    if hasattr(db, 'rollback'):
                        db.rollback()
                    
                    # Log the error
                    logger = getattr(self, 'logger', None)
                    if logger:
                        logger.error("Transaction failed: %s", str(e), exc_info=True)
                    
                    if propagate_errors:
                        raise
                    
                    # Re-raise with additional context
                    raise RuntimeError(f"Transaction failed: {str(e)}") from e
        
        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
    
    return decorator
