# app/utils/exceptions.py
"""
Custom exception classes for SketchDojo
"""


class SketchDojoException(Exception):
    """Base exception for SketchDojo"""


class ValidationError(SketchDojoException):
    """Raised when input validation fails"""


class EntityNotFoundError(SketchDojoException):
    """Raised when an entity is not found"""


class GenerationError(SketchDojoException):
    """Raised when generation process fails"""


class AIProviderError(SketchDojoException):
    """Raised when AI provider encounters an error"""


class ImageGenerationError(SketchDojoException):
    """Raised when image generation fails"""


class StorageError(SketchDojoException):
    """Raised when storage operations fail"""


class TaskError(SketchDojoException):
    """Raised when task processing fails"""
