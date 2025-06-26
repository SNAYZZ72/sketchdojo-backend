"""
Logging configuration and utilities for the application.

This module provides a centralized way to configure and access loggers
with consistent formatting and behavior across the application.
"""
import logging
import logging.config
import os
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    This function returns a logger with the specified name, configured with
    appropriate formatting and handlers. If no name is provided, it returns
    the root logger.
    
    Args:
        name: The name of the logger. If None, returns the root logger.
        
    Returns:
        A configured logging.Logger instance.
        
    Example:
        ```python
        # In a module
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        logger.info("This is an info message")
        ```
    """
    # Configure logging if not already configured
    if not logging.root.handlers:
        configure_logging()
    
    return logging.getLogger(name)

def configure_logging() -> None:
    """
    Configure the root logger with a standard format and console handler.
    
    This function should be called early in the application startup process.
    It configures the root logger with a console handler that uses a
    standardized log format.
    
    The log format includes:
    - Timestamp
    - Log level
    - Logger name
    - Process ID (if available)
    - Message
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Define the log format
    log_format = (
        "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
        "%(name)s:%(lineno)d - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
    )
    
    # Set log level for specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Add colors if colorlog is available
    try:
        import colorlog
        
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                f"%(log_color)s{log_format}",
                datefmt=date_format,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        )
        
        # Remove all handlers associated with the root logger
        for h in logging.root.handlers[:]:
            logging.root.removeHandler(h)
        
        # Add the new handler
        logging.root.addHandler(handler)
        
    except ImportError:
        # colorlog not available, use standard logging
        pass

# Configure logging when the module is imported
configure_logging()
