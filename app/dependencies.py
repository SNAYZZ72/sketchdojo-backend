# app/dependencies.py
"""
Dependency injection configuration for FastAPI
"""

import redis.asyncio as redis
from fastapi import Depends

from app.application.interfaces.ai_provider import AIProvider
from app.application.interfaces.image_generator import ImageGenerator
from app.application.interfaces.storage_provider import StorageProvider
from app.application.services.character_service import CharacterService
from app.application.services.chat_service import ChatService
from app.application.services.generation_service import GenerationService
from app.application.services.scene_service import SceneService
from app.application.services.webtoon_service import WebtoonService
from app.config import Settings, get_settings
from app.domain.repositories.chat_repository import ChatRepository
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.infrastructure.ai.openai_provider import OpenAIProvider
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.image.stability_provider import StabilityProvider
from app.infrastructure.repositories.chat_repository_redis import get_chat_repository
from app.websocket.handlers.chat_handler import ChatHandler
from app.infrastructure.storage.file_storage import FileStorage


def get_redis_client(
    settings: Settings = Depends(get_settings),
) -> redis.Redis:
    """Get Redis client instance"""
    return redis.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        decode_responses=True,
    )


def get_ai_provider(settings: Settings = Depends(get_settings)) -> AIProvider:
    """Get AI provider instance"""
    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
    )


def get_image_generator(
    settings: Settings = Depends(get_settings),
) -> ImageGenerator:
    """Get image generator instance"""
    return StabilityProvider(
        api_key=settings.stability_api_key, api_url=settings.stability_api_url
    )


def get_storage_provider(
    settings: Settings = Depends(get_settings),
) -> StorageProvider:
    """Get storage provider instance"""
    if settings.storage_type == "file":
        return FileStorage(settings.file_storage_path)
    elif settings.storage_type == "redis":
        from app.infrastructure.storage.redis_provider import RedisProvider
        return RedisProvider(settings.redis_url)
    else:
        # Default to file storage
        return FileStorage(settings.file_storage_path)


def get_redis_cache(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> RedisCache:
    """Get Redis cache instance"""
    return RedisCache(redis_client)


def get_webtoon_repository(
    storage: StorageProvider = Depends(get_storage_provider),
) -> WebtoonRepository:
    """Get webtoon repository instance"""
    return WebtoonRepository(storage)


def get_task_repository(
    storage: StorageProvider = Depends(get_storage_provider),
) -> TaskRepository:
    """Get task repository instance"""
    return TaskRepository(storage)


def get_webtoon_service(
    repository: WebtoonRepository = Depends(get_webtoon_repository),
) -> WebtoonService:
    """Get webtoon service instance"""
    return WebtoonService(repository)


def get_scene_service(
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> SceneService:
    """Get scene service instance"""
    return SceneService(ai_provider)


def get_character_service(
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> CharacterService:
    """Get character service instance"""
    return CharacterService(ai_provider)


def get_generation_service(
    ai_provider: AIProvider = Depends(get_ai_provider),
    image_generator: ImageGenerator = Depends(get_image_generator),
    webtoon_repository: WebtoonRepository = Depends(get_webtoon_repository),
    task_repository: TaskRepository = Depends(get_task_repository),
) -> GenerationService:
    """Get generation service instance"""
    return GenerationService(
        ai_provider=ai_provider,
        image_generator=image_generator,
        webtoon_repository=webtoon_repository,
        task_repository=task_repository,
    )


def get_redis_storage_provider(
    settings: Settings = Depends(get_settings),
) -> StorageProvider:
    """Get Redis-specific storage provider for chat functionality"""
    from app.infrastructure.storage.redis_provider import RedisProvider
    return RedisProvider(settings.redis_url)


async def get_chat_repository_dep(
    storage: StorageProvider = Depends(get_redis_storage_provider),
) -> ChatRepository:
    """Get chat repository instance"""
    return await get_chat_repository(storage)


async def get_chat_service(
    repository: ChatRepository = Depends(get_chat_repository_dep),
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> ChatService:
    """Get chat service instance"""
    return ChatService(repository, ai_provider)


# Global chat handler instance for dependency injection
_chat_handler = None


def get_chat_handler_dep(
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatHandler:
    """Get chat handler instance with proper dependency injection"""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler(chat_service)
    elif chat_service and not _chat_handler.chat_service:
        # Upgrade existing handler with chat service if needed
        _chat_handler.chat_service = chat_service
    return _chat_handler


async def get_chat_handler_for_websocket() -> ChatHandler:
    """Get chat handler instance directly for WebSocket use"""
    global _chat_handler
    # Initialize if needed
    if _chat_handler is None:
        # Get chat service manually
        storage_provider = get_redis_storage_provider(get_settings())
        chat_repo = await get_chat_repository(storage_provider)
        ai_provider = get_ai_provider(get_settings())
        chat_service = ChatService(chat_repo, ai_provider)
        _chat_handler = ChatHandler(chat_service)
    # Make sure chat service is set    
    if not _chat_handler.chat_service:
        # Get chat service manually
        storage_provider = get_redis_storage_provider(get_settings())
        chat_repo = await get_chat_repository(storage_provider)
        ai_provider = get_ai_provider(get_settings())
        _chat_handler.chat_service = ChatService(chat_repo, ai_provider)
    return _chat_handler
