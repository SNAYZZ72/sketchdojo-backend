# app/dependencies.py
"""
Dependency injection configuration for FastAPI
"""
import os
from functools import lru_cache
from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import Depends

from app.application.interfaces.ai_provider import AIProvider
from app.application.interfaces.image_generator import ImageGenerator
from app.application.interfaces.storage_provider import StorageProvider
from app.application.services.character_service import CharacterService
from app.application.services.generation_service import GenerationService
from app.application.services.scene_service import SceneService
from app.application.services.webtoon_service import WebtoonService
from app.config import Settings, get_settings
from app.domain.repositories.task_repository import TaskRepository
from app.domain.repositories.webtoon_repository import WebtoonRepository
from app.infrastructure.ai.openai_provider import OpenAIProvider
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.image.stability_provider import StabilityProvider
from app.infrastructure.storage.file_storage import FileStorage
from app.infrastructure.storage.memory_storage import MemoryStorage


def get_redis_client(settings: Settings = Depends(get_settings)) -> redis.Redis:
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


def get_image_generator(settings: Settings = Depends(get_settings)) -> ImageGenerator:
    """Get image generator instance"""
    return StabilityProvider(
        api_key=settings.stability_api_key, api_url=settings.stability_api_url
    )


def get_storage_provider(settings: Settings = Depends(get_settings)) -> StorageProvider:
    """Get storage provider instance"""
    if settings.storage_type == "memory":
        return MemoryStorage()
    elif settings.storage_type == "file":
        return FileStorage(settings.file_storage_path)
    else:
        # Default to memory storage
        return MemoryStorage()


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
