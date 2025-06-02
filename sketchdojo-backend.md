# SketchDojo Backend - Complete New Architecture

## Project Structure
```
sketchdojo-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management
│   ├── dependencies.py              # Dependency injection
│   │
│   ├── api/                         # API Layer (Controllers)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── webtoons.py      # Webtoon CRUD operations
│   │   │   │   ├── generation.py    # Generation endpoints
│   │   │   │   ├── tasks.py         # Task status endpoints
│   │   │   │   └── health.py        # Health check endpoints
│   │   │   └── dependencies.py      # Route-specific dependencies
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── cors.py              # CORS middleware
│   │       ├── logging.py           # Request logging
│   │       └── metrics.py           # Prometheus metrics
│   │
│   ├── application/                 # Application Layer (Use Cases)
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── webtoon_service.py   # Webtoon business logic
│   │   │   ├── generation_service.py # Generation orchestration
│   │   │   ├── scene_service.py     # Scene processing
│   │   │   └── character_service.py # Character management
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   ├── ai_provider.py       # AI provider interface
│   │   │   ├── image_generator.py   # Image generation interface
│   │   │   └── storage_provider.py  # Storage interface
│   │   └── dto/
│   │       ├── __init__.py
│   │       ├── webtoon_dto.py       # Data transfer objects
│   │       ├── generation_dto.py
│   │       └── task_dto.py
│   │
│   ├── domain/                      # Domain Layer (Core Business Logic)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── webtoon.py          # Webtoon entity
│   │   │   ├── panel.py            # Panel entity
│   │   │   ├── character.py        # Character entity
│   │   │   ├── scene.py            # Scene entity
│   │   │   └── generation_task.py  # Generation task entity
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── style.py            # Art style value object
│   │   │   ├── dimensions.py       # Panel dimensions
│   │   │   └── position.py         # Positioning data
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── webtoon_repository.py
│   │   │   ├── task_repository.py
│   │   │   └── base_repository.py
│   │   └── events/
│   │       ├── __init__.py
│   │       ├── generation_events.py
│   │       └── webtoon_events.py
│   │
│   ├── infrastructure/              # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── openai_provider.py   # OpenAI integration
│   │   │   └── prompt_templates.py  # Prompt management
│   │   ├── image/
│   │   │   ├── __init__.py
│   │   │   ├── stability_provider.py # Stability AI integration
│   │   │   └── image_processor.py   # Image processing utilities
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── memory_storage.py    # In-memory storage implementation
│   │   │   └── file_storage.py      # File system storage
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── redis_cache.py       # Redis caching
│   │   └── external/
│   │       ├── __init__.py
│   │       └── http_client.py       # HTTP client utilities
│   │
│   ├── tasks/                       # Celery Tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py           # Celery configuration
│   │   ├── generation_tasks.py      # Generation background tasks
│   │   ├── image_tasks.py          # Image processing tasks
│   │   └── notification_tasks.py   # Notification tasks
│   │
│   ├── websocket/                   # WebSocket Layer
│   │   ├── __init__.py
│   │   ├── connection_manager.py    # WebSocket connection management
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── generation_handler.py # Generation progress updates
│   │   │   └── chat_handler.py      # Real-time chat functionality
│   │   └── events.py               # WebSocket event definitions
│   │
│   ├── schemas/                     # Pydantic Schemas (API Models)
│   │   ├── __init__.py
│   │   ├── webtoon_schemas.py      # Webtoon API schemas
│   │   ├── generation_schemas.py   # Generation request/response schemas
│   │   ├── task_schemas.py         # Task status schemas
│   │   └── common_schemas.py       # Common/shared schemas
│   │
│   ├── monitoring/                  # Observability
│   │   ├── __init__.py
│   │   ├── metrics.py              # Prometheus metrics
│   │   ├── logging_config.py       # Structured logging setup
│   │   └── health_checks.py        # Health check implementations
│   │
│   └── utils/                       # Shared Utilities
│       ├── __init__.py
│       ├── exceptions.py           # Custom exceptions
│       ├── validators.py           # Input validation utilities
│       ├── helpers.py             # General helper functions
│       └── constants.py           # Application constants
│
├── tests/                          # Test Suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
│
├── docker/                        # Docker Configuration
│   ├── Dockerfile.api             # API service Dockerfile
│   ├── Dockerfile.worker          # Celery worker Dockerfile
│   └── docker-compose.yml         # Multi-service composition
│
├── scripts/                       # Utility Scripts
│   ├── start_development.sh       # Development startup script
│   ├── run_tests.sh              # Test runner script
│   └── deploy.sh                 # Deployment script
│
├── requirements/                  # Python Dependencies
│   ├── base.txt                  # Base requirements
│   ├── development.txt           # Development requirements
│   └── production.txt            # Production requirements
│
├── monitoring/                    # Monitoring Configuration
│   ├── prometheus.yml            # Prometheus configuration
│   ├── grafana/
│   │   ├── dashboards/          # Grafana dashboards
│   │   └── provisioning/        # Grafana provisioning
│   └── alerts/                  # Alert rules
│
├── .env.example                  # Environment variables template
├── .gitignore                   # Git ignore rules
├── pyproject.toml              # Python project configuration
└── README.md                   # Project documentation
```

## Key Architecture Decisions

### 1. Clean Architecture Implementation
- **Domain Layer**: Pure business logic, no external dependencies
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External integrations (AI, storage, etc.)
- **API Layer**: HTTP endpoints and WebSocket handlers

### 2. Dependency Injection
- FastAPI's built-in dependency injection system
- Interface-based dependencies for testability
- Easy swapping of implementations

### 3. Event-Driven Architecture
- Domain events for loose coupling
- WebSocket notifications for real-time updates
- Celery tasks for async processing

### 4. Observability First
- Structured logging with correlation IDs
- Prometheus metrics for monitoring
- Health checks for all external dependencies

### 5. Scalability Considerations
- Async/await throughout the stack
- Redis for caching and session management
- Celery for distributed task processing
- WebSocket connection management
