"""
Tests for the BaseService class.
"""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.application.services.base_service import BaseService, ServiceFactory
from app.core.error_handling.base_error_handler import BaseErrorHandler


class TestBaseService:
    """Tests for the BaseService class."""
    
    @pytest.fixture
    def mock_error_handler(self):
        """Create a mock error handler."""
        handler = MagicMock(spec=BaseErrorHandler)
        handler.handle_error = AsyncMock()
        return handler
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock(spec=logging.Logger)
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        # When
        service = BaseService()
        
        # Then
        assert service.error_handler is None
        assert isinstance(service.logger, logging.Logger)
    
    def test_init_with_custom_logger(self, mock_logger):
        """Test initialization with a custom logger."""
        # When
        service = BaseService(logger=mock_logger)
        
        # Then
        assert service.logger is mock_logger
    
    def test_init_with_error_handler(self, mock_error_handler):
        """Test initialization with an error handler."""
        # When
        service = BaseService(error_handler=mock_error_handler)
        
        # Then
        assert service.error_handler is mock_error_handler
    
    @pytest.mark.asyncio
    async def test_handle_error_with_handler(self, mock_error_handler):
        """Test handle_error when an error handler is configured."""
        # Given
        service = BaseService(error_handler=mock_error_handler)
        error = ValueError("Test error")
        context = {"key": "value"}
        
        # When
        service.handle_error(error, context)
        
        # Need to give the asyncio task time to run
        await asyncio.sleep(0.1)
        
        # Then
        mock_error_handler.handle_error.assert_awaited_once_with(error, context)
    
    def test_handle_error_without_handler(self, caplog):
        """Test handle_error when no error handler is configured."""
        # Given
        service = BaseService()
        error = ValueError("Test error")
        
        # When
        with caplog.at_level(logging.ERROR):
            service.handle_error(error)
        
        # Then
        assert "Unhandled error: Test error" in caplog.text
    
    def test_logging_methods(self, mock_logger):
        """Test the logging helper methods."""
        # Given
        service = BaseService(logger=mock_logger)
        message = "Test message"
        extra = {"key": "value"}
        
        # When/Then - Just verify the methods don't raise exceptions
        service.log_debug(message, **extra)
        service.log_info(message, **extra)
        service.log_warning(message, **extra)
        service.log_error(message, **extra)
        service.log_critical(message, **extra)
        
        # Verify the logger was called
        mock_logger.debug.assert_called_once_with(message, extra=extra)
        mock_logger.info.assert_called_once_with(message, extra=extra)
        mock_logger.warning.assert_called_once_with(message, extra=extra)
        mock_logger.error.assert_called_once_with(message, extra=extra)
        mock_logger.critical.assert_called_once_with(message, extra=extra)
    
    def test_get_dependencies(self):
        """Test getting dependencies from a service class."""
        # Given
        class TestService(BaseService):
            def __init__(self, repo: str, service: int, config: dict):
                super().__init__()
        
        # When
        deps = TestService.get_dependencies()
        
        # Then
        assert deps == {
            'repo': str,
            'service': int,
            'config': dict,
        }


class TestServiceFactory:
    """Tests for the ServiceFactory class."""
    
    def test_create_service_with_direct_dependencies(self):
        """Test creating a service with direct dependencies."""
        # Given
        class TestService(BaseService):
            def __init__(self, repo: str, service: int):
                super().__init__()
                self.repo = repo
                self.service = service
        
        # When
        factory = ServiceFactory(TestService, repo="test_repo", service=42)
        service = factory.create()
        
        # Then
        assert isinstance(service, TestService)
        assert service.repo == "test_repo"
        assert service.service == 42
    
    def test_create_service_with_type_matching(self):
        """Test creating a service with type-based dependency injection."""
        # Given
        class Repo:
            pass
            
        class Service:
            pass
            
        class TestService(BaseService):
            def __init__(self, repo: Repo, service: Service):
                super().__init__()
                self.repo = repo
                self.service = service
        
        repo = Repo()
        service = Service()
        
        # When
        factory = ServiceFactory(TestService, repo=repo, service=service)
        result = factory.create()
        
        # Then
        assert result.repo is repo
        assert result.service is service
    
    def test_create_service_with_overrides(self):
        """Test creating a service with dependency overrides."""
        # Given
        class TestService(BaseService):
            def __init__(self, repo: str, service: int):
                super().__init__()
                self.repo = repo
                self.service = service
        
        # When
        factory = ServiceFactory(TestService, repo="original", service=42)
        service = factory.create(repo="overridden")
        
        # Then
        assert service.repo == "overridden"
        assert service.service == 42
    
    def test_missing_dependency_raises_error(self):
        """Test that a missing dependency raises an error."""
        # Given
        class TestService(BaseService):
            def __init__(self, repo: str):
                super().__init__()
        
        # When/Then
        factory = ServiceFactory(TestService)
        with pytest.raises(ValueError) as excinfo:
            factory.create()
        
        assert "Missing dependency 'repo' of type str" in str(excinfo.value)
