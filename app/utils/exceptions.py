# app/utils/exceptions.py
"""
Custom exception classes for SketchDojo
"""


class SketchDojoException(Exception):
    """Base exception for SketchDojo"""

    pass


class ValidationError(SketchDojoException):
    """Raised when input validation fails"""

    pass


class EntityNotFoundError(SketchDojoException):
    """Raised when an entity is not found"""

    pass


class GenerationError(SketchDojoException):
    """Raised when generation process fails"""

    pass


class AIProviderError(SketchDojoException):
    """Raised when AI provider encounters an error"""

    pass


class ImageGenerationError(SketchDojoException):
    """Raised when image generation fails"""

    pass


class StorageError(SketchDojoException):
    """Raised when storage operations fail"""

    pass


class TaskError(SketchDojoException):
    """Raised when task processing fails"""

    pass
