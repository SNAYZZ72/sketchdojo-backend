"""
Base service class providing common functionality for all services.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar, get_type_hints

from app.core.error_handling.base_error_handler import BaseErrorHandler

T = TypeVar('T')


class BaseService(ABC):
    """
    Abstract base class for all services in the application.
    
    This class provides common functionality such as:
    - Logging
    - Error handling
    - Dependency injection
    - Common utility methods
    """
    
    def __init__(self, 
                error_handler: Optional[BaseErrorHandler] = None,
                logger: Optional[logging.Logger] = None):
        """
        Initialize the base service.
        
        Args:
            error_handler: Optional error handler instance
            logger: Optional logger instance (defaults to module-level logger)
        """
        self._logger = logger or logging.getLogger(self.__class__.__module__)
        self._error_handler = error_handler
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance for this service."""
        return self._logger
    
    @property
    def error_handler(self) -> Optional[BaseErrorHandler]:
        """Get the error handler instance for this service."""
        return self._error_handler
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Handle an error using the service's error handler.
        
        Args:
            error: The exception to handle
            context: Optional context about the error
        """
        if self._error_handler:
            # Run in the background to avoid blocking
            import asyncio
            asyncio.create_task(self._error_handler.handle_error(error, context))
        else:
            self._logger.error("Unhandled error: %s", str(error), exc_info=True, extra={"context": context or {}})
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log a debug message with additional context."""
        self._logger.debug(message, extra=kwargs)
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log an info message with additional context."""
        self._logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log a warning message with additional context."""
        self._logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs) -> None:
        """Log an error message with additional context."""
        self._logger.error(message, extra=kwargs)
    
    def log_critical(self, message: str, **kwargs) -> None:
        """Log a critical message with additional context."""
        self._logger.critical(message, extra=kwargs)
    
    @classmethod
    def get_dependencies(cls) -> Dict[str, Type]:
        """
        Get the service's dependencies from its type hints.
        
        Returns:
            Dictionary of parameter names to their types for dependencies
        """
        # Get the __init__ method
        init = getattr(cls, "__init__", None)
        if not init:
            return {}
            
        # Get type hints for the __init__ method
        hints = get_type_hints(init)
        
        # Filter out 'self' and return type
        return {name: type_ for name, type_ in hints.items() 
                if name != 'return' and name != 'self'}


class ServiceFactory(Generic[T]):
    """
    Factory class for creating service instances with dependency injection.
    """
    
    def __init__(self, service_class: Type[T], **dependencies):
        """
        Initialize the service factory.
        
        Args:
            service_class: The service class to instantiate
            **dependencies: Dependencies to inject into the service
        """
        self._service_class = service_class
        self._dependencies = dependencies
    
    def create(self, **override_deps) -> T:
        """
        Create a new instance of the service with dependencies injected.
        
        Args:
            **override_deps: Dependencies to override
            
        Returns:
            A new instance of the service
        """
        # Combine default and override dependencies
        deps = {**self._dependencies, **override_deps}
        
        # Get the service's dependencies from type hints
        required_deps = self._service_class.get_dependencies()
        
        # Prepare the dependencies to pass to the service
        dep_kwargs = {}
        for name, dep_type in required_deps.items():
            if name in deps:
                dep_kwargs[name] = deps[name]
            else:
                # Try to find a dependency of the required type
                matching_deps = [dep for dep in deps.values() if isinstance(dep, dep_type)]
                if matching_deps:
                    dep_kwargs[name] = matching_deps[0]
                else:
                    raise ValueError(f"Missing dependency '{name}' of type {dep_type.__name__}")
        
        # Create and return the service instance
        return self._service_class(**dep_kwargs)
