# Repository Pattern Implementation

This directory contains the implementation of the repository pattern for data access in the application. The repository pattern provides an abstraction of data, so that your application can work with a simple abstraction that has an interface approximating that of a collection.

## Base Repository

The `BaseRedisRepository` class provides common CRUD operations for Redis-based repositories. It implements the `BaseRepository` interface and adds Redis-specific functionality.

### Features

- Standardized CRUD operations
- Built-in error handling and logging
- Support for TTL (Time To Live) on keys
- Pagination and filtering support
- Serialization/deserialization hooks

### Usage

```python
from typing import Type, TypeVar
from uuid import UUID
from app.infrastructure.repositories.base_redis_repository import BaseRedisRepository

T = TypeVar('T', bound='YourEntity')

class YourRepository(BaseRedisRepository[T]):
    def __init__(self, storage: StorageProvider):
        super().__init__(
            storage=storage,
            key_prefix="your:prefix",
            ttl_seconds=86400  # Optional TTL in seconds
        )
    
    @property
    def entity_class(self) -> Type[T]:
        return YourEntity
    
    def _serialize_entity(self, entity: T) -> str:
        # Custom serialization logic
        return json.dumps(entity.dict())
    
    def _deserialize_entity(self, data: str, entity_class: Type[T] = None) -> T:
        # Custom deserialization logic
        data_dict = json.loads(data) if isinstance(data, str) else data
        return entity_class(**data_dict)
```

## Key Generation

The `KeyGenerator` utility provides consistent key generation for Redis storage.

### Features

- Consistent key formatting
- Support for different data types (strings, UUIDs, numbers)
- Namespace support
- Pattern generation for scanning
- Customizable separators

### Usage

```python
from app.infrastructure.utils.key_generator import KeyGenerator, chat_keys

# Basic key generation
key = KeyGenerator.generate_key("chat", "message", "123")  # "chat:message:123"

# Pattern generation
pattern = KeyGenerator.generate_pattern("chat", "message", "*")  # "chat:message:*"

# Namespaced key generator
ns = KeyGenerator.for_namespace("chat")
key = ns.key("message", "123")  # "chat:message:123"
pattern = ns.pattern("message", "*")  # "chat:message:*"

# Predefined chat keys
message_key = chat_keys.message("123")  # "chat:message:123"
room_key = chat_keys.room("456")  # "chat:room:456"
```

## Best Practices

1. **Consistent Key Structure**: Always use the `KeyGenerator` to ensure consistent key structure across the application.

2. **Use Namespaced Keys**: Group related keys under appropriate namespaces (e.g., `chat:message:123`, `user:profile:456`).

3. **Implement TTL**: Set appropriate TTL values for temporary data to prevent memory leaks.

4. **Handle Serialization**: Implement proper serialization/deserialization in your repository classes.

5. **Error Handling**: Let the base repository handle common errors, but implement custom error handling when needed.

## Testing

Unit tests for the repository and key generation utilities can be found in:
- `tests/unit/infrastructure/repositories/test_base_redis_repository.py`
- `tests/unit/infrastructure/utils/test_key_generator.py`

## Dependencies

- Redis storage provider
- Pydantic (for model serialization)
- Python's built-in `json` module

## Related Components

- `app/application/interfaces/storage_provider.py` - Storage provider interface
- `app/domain/repositories/base_repository.py` - Base repository interface
- `app/domain/entities/` - Domain entities
