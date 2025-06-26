"""
Error handling mixins for repository implementations.

This module provides reusable error handling functionality that can be mixed into
repository classes to provide consistent error handling and logging.
"""
import logging
from typing import Any, Callable, Optional, Type, TypeVar, cast

from pydantic import BaseModel

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    """Base exception for repository-related errors."""
    pass

class NotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""
    pass

class AlreadyExistsError(RepositoryError):
    """Raised when trying to create an entity that already exists."""
    pass

class OptimisticLockError(RepositoryError):
    """Raised when an optimistic lock fails during an update."""
    pass

class ErrorHandlingMixin:
    """
    A mixin class that provides common error handling functionality for repositories.
    """
    
    @classmethod
    def handle_operation(
        cls,
        operation: Callable[..., T],
        *args: Any,
        not_found_error: bool = False,
        not_found_message: Optional[str] = None,
        already_exists_error: bool = False,
        **kwargs: Any
    ) -> T:
        """
        Execute a repository operation with standardized error handling.
        
        Args:
            operation: The repository operation to execute
            *args: Positional arguments to pass to the operation
            not_found_error: If True, raises NotFoundError when the operation returns None
            not_found_message: Custom message for NotFoundError
            already_exists_error: If True, raises AlreadyExistsError when the operation returns False
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            The result of the operation
            
        Raises:
            NotFoundError: If not_found_error is True and operation returns None
            AlreadyExistsError: If already_exists_error is True and operation returns False
            RepositoryError: For other unexpected errors
        """
        try:
            result = operation(*args, **kwargs)
            
            # Handle the case where the operation returns None
            if result is None and not_found_error:
                raise NotFoundError(not_found_message or "Resource not found")
                
            # Handle the case where the operation returns False (for create operations)
            if result is False and already_exists_error:
                raise AlreadyExistsError("Resource already exists")
                
            return result
            
        except (NotFoundError, AlreadyExistsError, OptimisticLockError):
            # Re-raise these specific exceptions as-is
            raise
            
        except Exception as e:
            # Log the error and wrap in a RepositoryError
            logger.exception(
                "Error in repository operation %s: %s",
                getattr(operation, '__name__', str(operation)),
                str(e)
            )
            raise RepositoryError(f"Repository operation failed: {str(e)}") from e
    
    @classmethod
    async def handle_async_operation(
        cls,
        operation: Callable[..., T],
        *args: Any,
        not_found_error: bool = False,
        not_found_message: Optional[str] = None,
        already_exists_error: bool = False,
        **kwargs: Any
    ) -> T:
        """
        Execute an async repository operation with standardized error handling.
        
        Args:
            operation: The async repository operation to execute
            *args: Positional arguments to pass to the operation
            not_found_error: If True, raises NotFoundError when the operation returns None
            not_found_message: Custom message for NotFoundError
            already_exists_error: If True, raises AlreadyExistsError when the operation returns False
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            The result of the operation
            
        Raises:
            NotFoundError: If not_found_error is True and operation returns None
            AlreadyExistsError: If already_exists_error is True and operation returns False
            RepositoryError: For other unexpected errors
        """
        try:
            # Await the async operation
            result = await operation(*args, **kwargs)
            
            # Handle the case where the operation returns None
            if result is None and not_found_error:
                raise NotFoundError(not_found_message or "Resource not found")
                
            # Handle the case where the operation returns False (for create operations)
            if result is False and already_exists_error:
                raise AlreadyExistsError("Resource already exists")
                
            return result
            
        except (NotFoundError, AlreadyExistsError, OptimisticLockError):
            # Re-raise these specific exceptions as-is
            raise
            
        except Exception as e:
            # Log the error and wrap in a RepositoryError
            logger.exception(
                "Error in async repository operation %s: %s",
                getattr(operation, '__name__', str(operation)),
                str(e)
            )
            raise RepositoryError(f"Async repository operation failed: {str(e)}") from e

class EntityValidationMixin:
    """
    A mixin class that provides entity validation functionality.
    """
    
    @classmethod
    def validate_entity(
        cls,
        entity: Any,
        entity_type: Type[BaseModel],
        context: Optional[dict] = None
    ) -> BaseModel:
        """
        Validate an entity against a Pydantic model.
        
        Args:
            entity: The entity to validate
            entity_type: The Pydantic model class to validate against
            context: Optional validation context
            
        Returns:
            The validated entity as a Pydantic model
            
        Raises:
            ValueError: If validation fails
        """
        try:
            if context:
                return entity_type.model_validate(entity, context=context)
            return entity_type.model_validate(entity)
        except Exception as e:
            logger.error(
                "Failed to validate entity %s: %s",
                entity_type.__name__,
                str(e),
                exc_info=True
            )
            raise ValueError(f"Invalid {entity_type.__name__}: {str(e)}") from e
