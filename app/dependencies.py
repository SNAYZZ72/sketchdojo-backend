# app/dependencies.py
"""
Dependency injection configuration for FastAPI
"""

import redis.asyncio as redis
from fastapi import Depends

from app.application.interfaces.ai_provider import AIProvider
from app.application.interfaces.image_generator import ImageGenerator
from app.application.interfaces.storage_provider import StorageProvider
from app.application.services.chat_service import ChatService
from app.application.services.character_service import CharacterService
from app.application.services.generation_service import GenerationService, create_generation_service
from app.application.services.scene_service import SceneService
from app.application.services.webtoon_service import WebtoonService
from app.config import Settings, get_settings
from app.domain.repositories.chat_repository import ChatRepository
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.infrastructure.ai.openai_provider import OpenAIProvider
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.image.stability_provider import StabilityProvider
from app.infrastructure.repositories.chat_repository_redis import ChatRepositoryRedis
from app.websocket.handlers.chat_handler import ChatHandler
from app.infrastructure.storage.file_storage import FileStorage
from app.utils.webtoon_renderer import WebtoonRenderer


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


def create_storage_provider(settings: Settings) -> StorageProvider:
    """Create a storage provider instance based on settings
    This function can be called from anywhere, not just within FastAPI's dependency injection system
    """
    if settings.storage_type == "file":
        return FileStorage(settings.file_storage_path)
    elif settings.storage_type == "redis":
        from app.infrastructure.storage.redis_storage import RedisStorage
        return RedisStorage(settings.redis_url)
    else:
        # Default to file storage
        return FileStorage(settings.file_storage_path)


def get_storage_provider(
    settings: Settings = Depends(get_settings),
) -> StorageProvider:
    """Get storage provider instance as a FastAPI dependency"""
    return create_storage_provider(settings)


def get_redis_cache(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> RedisCache:
    """Get Redis cache instance"""
    return RedisCache(redis_client)


def get_webtoon_repository(
    storage: StorageProvider = Depends(get_storage_provider),
) -> WebtoonRepository:
    """Get webtoon repository instance"""
    from app.domain.mappers.webtoon_mapper import WebtoonDataMapper
    return WebtoonRepository(storage, mapper=WebtoonDataMapper())


def get_task_repository(
    storage: StorageProvider = Depends(get_storage_provider),
) -> TaskRepository:
    """Get task repository instance"""
    from app.domain.mappers.task_mapper import TaskDataMapper
    return TaskRepository(storage, mapper=TaskDataMapper())


def get_webtoon_renderer() -> WebtoonRenderer:
    """Get webtoon renderer instance"""
    return WebtoonRenderer()


def get_webtoon_service(
    repository: WebtoonRepository = Depends(get_webtoon_repository),
    renderer: WebtoonRenderer = Depends(get_webtoon_renderer),
) -> WebtoonService:
    """Get webtoon service instance"""
    return WebtoonService(repository=repository, renderer=renderer)


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
    """
    Get generation service instance using the factory function.
    
    Returns:
        GenerationService: Configured instance of GenerationService with all dependencies injected
    """
    return create_generation_service(
        ai_provider=ai_provider,
        image_generator=image_generator,
        webtoon_repository=webtoon_repository,
        task_repository=task_repository,
    )


async def get_chat_repository_dep(
    storage: StorageProvider = Depends(get_storage_provider),
) -> ChatRepository:
    """Get chat repository instance"""
    return ChatRepositoryRedis(storage=storage)


async def get_chat_service(
    repository: ChatRepository = Depends(get_chat_repository_dep),
    ai_provider: AIProvider = Depends(get_ai_provider),
    webtoon_repository: WebtoonRepository = Depends(get_webtoon_repository),
) -> ChatService:
    """Get chat service instance with all required dependencies"""
    return ChatService(repository, ai_provider, webtoon_repository)


# Dependency factory for ChatHandler
class ChatHandlerFactory:
    """Factory for creating ChatHandler instances"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton factory instance"""
        if cls._instance is None:
            cls._instance = ChatHandlerFactory()
        return cls._instance
    
    def __init__(self):
        self._handler = None
        
    def get_handler(self, chat_service: ChatService = None) -> ChatHandler:
        """Get or create a ChatHandler instance"""
        if self._handler is None:
            self._handler = ChatHandler(chat_service)
        elif chat_service and not self._handler.chat_service:
            # Upgrade existing handler with chat service if needed
            self._handler.chat_service = chat_service
        return self._handler


def get_chat_handler_dep(
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatHandler:
    """Get chat handler instance with proper dependency injection"""
    return ChatHandlerFactory.get_instance().get_handler(chat_service)


async def get_chat_handler_for_websocket() -> ChatHandler:
    """Get chat handler instance directly for WebSocket use"""
    # Only create dependencies if handler doesn't exist or lacks chat service
    factory = ChatHandlerFactory.get_instance()
    handler = factory.get_handler()
    
    if not handler.chat_service:
        # Get chat service manually
        storage_provider = create_storage_provider(get_settings())
        chat_repo = ChatRepositoryRedis(storage=storage_provider)
        ai_provider = get_ai_provider(get_settings())
        webtoon_repo = get_webtoon_repository(storage_provider)
        chat_service = ChatService(chat_repo, ai_provider, webtoon_repo)
        # Update handler with service
        handler.chat_service = chat_service
        
    return handler
