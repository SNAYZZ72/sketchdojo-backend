# SketchDojo Backend - Comprehensive Guide

## 🏗️ Architecture Overview

SketchDojo Backend is built with **Clean Architecture** principles and **Domain-Driven Design** to ensure scalability, maintainability, and testability.

### System Components

```mermaid
graph TB
    Client[Client Applications] --> LB[Load Balancer/Nginx]
    LB --> API[FastAPI Application]
    API --> Auth[Authentication Layer]
    API --> WS[WebSocket Manager]
    API --> Cache[Redis Cache]
    
    API --> BG[Background Tasks]
    BG --> Celery[Celery Workers]
    Celery --> AI[AI Services]
    AI --> OpenAI[OpenAI GPT-4]
    AI --> Stability[Stability AI]
    
    API --> DB[(MySQL Database)]
    API --> Storage[File Storage]
    Storage --> Local[Local Storage]
    Storage --> S3[AWS S3]
    
    Monitor[Monitoring Stack]
    Monitor --> Prometheus[Prometheus]
    Monitor --> Grafana[Grafana]
    Monitor --> Jaeger[Jaeger Tracing]
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API Framework** | FastAPI + Uvicorn | High-performance async web framework |
| **Database** | MySQL 8.0 + SQLAlchemy | Persistent data storage with async ORM |
| **Cache** | Redis 7.0 | Session management, caching, message broker |
| **Task Queue** | Celery | Background processing for AI operations |
| **Authentication** | JWT + bcrypt | Secure token-based authentication |
| **AI Integration** | OpenAI + Stability AI | LLM and image generation services |
| **Monitoring** | Prometheus + Grafana | Metrics collection and visualization |
| **Tracing** | Jaeger | Distributed request tracing |
| **Storage** | Local/S3 | File storage abstraction |
| **Containerization** | Docker + Compose | Development and deployment |
| **Orchestration** | Kubernetes | Production container orchestration |

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **MySQL 8.0** (or use Docker)
- **Redis 7.0** (or use Docker)

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sketchdojo/backend.git
   cd sketchdojo-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements/dev.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Required Environment Variables:**
   ```bash
   # Database
   DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/sketchdojo
   
   # Redis
   REDIS_URL=redis://localhost:6379/0
   
   # AI Services (Required)
   OPENAI_API_KEY=your-openai-api-key-here
   STABILITY_AI_API_KEY=your-stability-ai-api-key-here
   
   # Security
   SECRET_KEY=your-secret-key-here
   ```

### Development Setup

1. **Start services with Docker:**
   ```bash
   make docker-up
   # Or manually:
   docker-compose -f docker/docker-compose.dev.yml up -d
   ```

2. **Initialize database:**
   ```bash
   make init-db
   # Or manually:
   python scripts/init_db.py
   ```

3. **Run development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Start Celery worker (separate terminal):**
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

### Verify Installation

- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Grafana Dashboard:** http://localhost:3000 (admin/admin)
- **Prometheus Metrics:** http://localhost:9090

## 📚 API Usage Examples

### Authentication Flow

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123"
  }'

# 2. Login to get tokens
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePassword123"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Project Management

```bash
# Set your access token
TOKEN="your-access-token-here"

# 1. Create a project
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Epic Webtoon",
    "description": "A story about heroes and villains",
    "art_style": "webtoon",
    "target_panels": 8,
    "story_outline": "A young hero discovers magical powers..."
  }'

# Response:
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "My Epic Webtoon",
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Character Creation

```bash
PROJECT_ID="123e4567-e89b-12d3-a456-426614174000"

# Create a character
curl -X POST "http://localhost:8000/api/v1/characters?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alex Thunder",
    "role": "protagonist",
    "description": "A brave young mage with lightning powers",
    "appearance": {
      "age_range": "young_adult",
      "gender": "male",
      "height": "tall",
      "build": "athletic",
      "hair_color": "silver",
      "hair_style": "spiky",
      "eye_color": "electric_blue",
      "skin_tone": "fair",
      "distinctive_features": ["lightning-shaped scar on forehead"]
    },
    "personality": {
      "traits": ["brave", "impulsive", "loyal"],
      "motivations": ["protect innocent people", "master lightning magic"],
      "fears": ["losing control of powers", "failing friends"],
      "speech_style": "confident"
    }
  }'
```

### Webtoon Generation

```bash
# Start webtoon generation
curl -X POST "http://localhost:8000/api/v1/webtoons/generate?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "story_prompt": "Alex discovers his lightning powers during a storm and must save his village from shadow monsters",
    "character_descriptions": ["Young mage with silver hair and lightning powers"],
    "style_preferences": {
      "style": "webtoon",
      "quality": "high",
      "color_scheme": "vibrant"
    },
    "panel_count": 6,
    "auto_generate_panels": true
  }'

# Response:
{
  "id": "task-456e7890-e89b-12d3-a456-426614174000",
  "status": "pending",
  "progress": 0.0,
  "created_at": "2024-01-15T10:45:00Z"
}
```

### Task Monitoring

```bash
TASK_ID="task-456e7890-e89b-12d3-a456-426614174000"

# Check task status
curl -X GET "http://localhost:8000/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "id": "task-456e7890-e89b-12d3-a456-426614174000",
  "status": "running",
  "progress": 65.0,
  "current_step": "Generating panel 4 of 6",
  "started_at": "2024-01-15T10:45:05Z",
  "estimated_duration_seconds": 300
}
```

### WebSocket Real-time Updates

```javascript
// JavaScript WebSocket client example
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/connect?token=your-access-token');

ws.onopen = function(event) {
    console.log('Connected to SketchDojo WebSocket');
    
    // Subscribe to task updates
    ws.send(JSON.stringify({
        type: 'subscribe_task',
        task_id: 'task-456e7890-e89b-12d3-a456-426614174000'
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    if (message.type === 'task_update') {
        console.log(`Task ${message.task_id}: ${message.data.progress}% complete`);
        console.log(`Current step: ${message.data.current_step}`);
    }
};
```

## 🏭 Production Deployment

### Docker Compose Deployment

```bash
# 1. Build and deploy
./scripts/deploy.sh production

# 2. Or manually:
docker-compose -f docker/docker-compose.yml up -d

# 3. Check status
docker-compose ps
```

### Kubernetes Deployment

```bash
# 1. Deploy to Kubernetes
./scripts/deploy.sh kubernetes

# 2. Or manually:
kubectl apply -f deployment/kubernetes/

# 3. Check pods
kubectl get pods -n sketchdojo
```

### Environment-Specific Configuration

#### Production Environment Variables

```bash
# Production .env
ENVIRONMENT=production
DEBUG=false

# Database (use managed service)
DATABASE_URL=mysql+asyncmy://user:password@db-cluster:3306/sketchdojo

# Redis (use managed service)
REDIS_URL=redis://redis-cluster:6379/0

# AI Services (production keys)
OPENAI_API_KEY=sk-prod-...
STABILITY_AI_API_KEY=sk-prod-...

# Storage (use S3 in production)
STORAGE_TYPE=s3
S3_BUCKET_NAME=sketchdojo-prod-storage
S3_REGION=us-east-1

# Security (strong keys)
SECRET_KEY=prod-secret-key-256-bits-long

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=WARNING
```

### Health Checks and Monitoring

The system includes comprehensive health monitoring:

```bash
# Application health
curl http://localhost:8000/health

# Detailed health with dependencies
curl http://localhost:8000/health/readiness

# Prometheus metrics
curl http://localhost:8000/metrics
```

## 🔧 Development Workflow

### Code Quality Standards

```bash
# Format code
make format

# Lint code
make lint

# Run tests
make test

# Run specific test categories
make test-unit
make test-integration
```

### Database Migrations

```bash
# Create a new migration
python scripts/create_migration.py "Add user preferences table"

# Apply migrations
python scripts/migrate.py upgrade

# Check migration status
python scripts/migrate.py current
```

### Adding New Features

1. **Domain Model** (`app/domain/models/`)
   ```python
   @dataclass
   class NewFeature(DomainEntity):
       name: str
       description: str
   ```

2. **Database Model** (`app/infrastructure/database/models/`)
   ```python
   class NewFeatureModel(BaseModel):
       __tablename__ = "new_features"
       name = Column(String(100), nullable=False)
   ```

3. **Repository** (`app/infrastructure/database/repositories/`)
   ```python
   class NewFeatureRepository(BaseRepository[NewFeature]):
       async def get_by_name(self, name: str) -> Optional[NewFeature]:
           # Implementation
   ```

4. **Service** (`app/domain/services/`)
   ```python
   class NewFeatureService:
       def __init__(self, repo: NewFeatureRepository):
           self.repo = repo
   ```

5. **API Endpoint** (`app/api/v1/endpoints/`)
   ```python
   @router.post("", response_model=NewFeatureResponse)
   async def create_feature(data: NewFeatureCreate):
       # Implementation
   ```

6. **Tests** (`tests/`)
   ```python
   @pytest.mark.asyncio
   async def test_create_feature():
       # Test implementation
   ```

## 🐛 Troubleshooting Guide

### Common Issues

#### 1. Database Connection Errors

**Symptom:** `Can't connect to MySQL server`

**Solutions:**
```bash
# Check if MySQL is running
docker ps | grep mysql

# Check database URL format
echo $DATABASE_URL

# Test connection manually
mysql -h localhost -u sketchdojo -p sketchdojo
```

#### 2. Redis Connection Errors

**Symptom:** `Redis connection failed`

**Solutions:**
```bash
# Check Redis status
docker ps | grep redis

# Test Redis connection
redis-cli ping

# Check Redis URL
echo $REDIS_URL
```

#### 3. AI Service Errors

**Symptom:** `OpenAI API key invalid`

**Solutions:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check API quotas and billing
```

#### 4. Task Queue Issues

**Symptom:** Tasks stuck in pending state

**Solutions:**
```bash
# Check Celery workers
celery -A app.core.celery_app inspect active

# Restart workers
celery -A app.core.celery_app control purge

# Check Redis broker
redis-cli -n 1 keys "*"
```

#### 5. WebSocket Connection Issues

**Symptom:** WebSocket connections failing

**Solutions:**
```bash
# Check authentication token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me

# Test WebSocket endpoint
wscat -c "ws://localhost:8000/api/v1/ws/connect?token=$TOKEN"

# Check CORS settings
echo $CORS_ORIGINS
```

### Performance Optimization

#### Database Performance

```python
# Use connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=50

# Add database indexes
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_panels_webtoon_id ON panels(webtoon_id);
CREATE INDEX idx_tasks_status ON tasks(status);
```

#### Caching Strategy

```python
# Cache frequently accessed data
@cache_service.cached(ttl=3600, key_template="user:{0}")
async def get_user_profile(user_id: UUID):
    return await user_repo.get_by_id(user_id)

# Invalidate cache on updates
@cache_service.cache_invalidate(pattern="user:{0}:*")
async def update_user(user_id: UUID, data):
    return await user_repo.update(user_id, data)
```

#### Background Task Optimization

```python
# Use appropriate task queues
celery_app.conf.task_routes = {
    'app.tasks.ai_tasks.*': {'queue': 'ai_processing'},
    'app.tasks.image_tasks.*': {'queue': 'image_generation'},
}

# Set task priorities
@celery_app.task(bind=True, priority=9)
def high_priority_task(self):
    pass
```

### Monitoring and Alerts

#### Key Metrics to Monitor

- **Response Times:** API endpoint latency
- **Error Rates:** HTTP 4xx/5xx responses
- **Task Queue:** Pending/failed tasks
- **Database:** Connection pool usage
- **Memory:** Application memory usage
- **AI Services:** API call success rates

#### Grafana Dashboard Queries

```promql
# API Response Time
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Error Rate
rate(http_requests_total{status_code=~"5.."}[5m])

# Active Tasks
celery_tasks_total{status="running"}

# Database Connections
database_connections_active
```

## 📖 API Reference

### Base URL
- **Development:** `http://localhost:8000`
- **Production:** `https://api.sketchdojo.com`

### Authentication
All API endpoints except `/auth/register` and `/auth/login` require authentication.

**Header Format:**
```
Authorization: Bearer {access_token}
```

### Rate Limits
- **General API:** 60 requests/minute
- **AI Generation:** 100 requests/hour
- **Image Generation:** 50 requests/hour

### Response Formats

#### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Response
```json
{
  "status": "error",
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "field": "error description"
  }
}
```

#### Paginated Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### Complete Endpoint List

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Authentication** |
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh tokens |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/logout` | User logout |
| **Projects** |
| GET | `/api/v1/projects` | List user projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}` | Get project |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |
| **Characters** |
| GET | `/api/v1/characters/project/{id}` | List project characters |
| POST | `/api/v1/characters` | Create character |
| GET | `/api/v1/characters/{id}` | Get character |
| PUT | `/api/v1/characters/{id}` | Update character |
| DELETE | `/api/v1/characters/{id}` | Delete character |
| **Webtoons** |
| POST | `/api/v1/webtoons` | Create webtoon |
| GET | `/api/v1/webtoons/{id}` | Get webtoon |
| PUT | `/api/v1/webtoons/{id}` | Update webtoon |
| POST | `/api/v1/webtoons/generate` | Generate webtoon |
| POST | `/api/v1/webtoons/{id}/publish` | Publish webtoon |
| **Panels** |
| GET | `/api/v1/panels/webtoon/{id}` | List webtoon panels |
| POST | `/api/v1/panels` | Create panel |
| GET | `/api/v1/panels/{id}` | Get panel |
| PUT | `/api/v1/panels/{id}` | Update panel |
| DELETE | `/api/v1/panels/{id}` | Delete panel |
| POST | `/api/v1/panels/generate` | Generate panel |
| **Tasks** |
| GET | `/api/v1/tasks` | List user tasks |
| GET | `/api/v1/tasks/{id}` | Get task status |
| POST | `/api/v1/tasks/{id}/cancel` | Cancel task |
| POST | `/api/v1/tasks/{id}/retry` | Retry failed task |
| **WebSocket** |
| WS | `/api/v1/ws/connect` | Real-time updates |

## 🤝 Contributing

### Development Setup for Contributors

1. **Fork and clone:**
   ```bash
   git clone https://github.com/yourusername/sketchdojo-backend.git
   cd sketchdojo-backend
   ```

2. **Set up pre-commit hooks:**
   ```bash
   make dev
   ```

3. **Create feature branch:**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

4. **Make changes and test:**
   ```bash
   make test
   make lint
   ```

5. **Submit pull request**

### Code Style Guidelines

- **Python:** Follow PEP 8, use Black formatter
- **Imports:** Use isort for import organization
- **Type Hints:** Required for all public functions
- **Documentation:** Docstrings for all classes and methods
- **Testing:** Maintain >90% test coverage

### Commit Message Format

```
type(scope): short description

Longer description if needed

Fixes #123
```

**Types:** feat, fix, docs, style, refactor, test, chore

## 📞 Support

- **Documentation:** https://docs.sketchdojo.com
- **Issues:** https://github.com/sketchdojo/backend/issues
- **Discussions:** https://github.com/sketchdojo/backend/discussions
- **Email:** support@sketchdojo.com

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by the SketchDojo Team**

*Empowering creators to bring their stories to life through AI-powered webtoon creation.*



## Project Root Structure
```
sketchdojo-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── core/                       # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py              # Application configuration
│   │   ├── database.py            # Database configuration
│   │   ├── redis.py               # Redis configuration
│   │   ├── celery_app.py          # Celery configuration
│   │   ├── websocket.py           # WebSocket manager
│   │   ├── dependencies.py        # FastAPI dependencies
│   │   ├── exceptions.py          # Custom exceptions
│   │   ├── middleware.py          # Custom middleware
│   │   └── logging.py             # Logging configuration
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── router.py              # Main API router
│   │   ├── v1/                    # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py        # Authentication endpoints
│   │   │   │   ├── projects.py    # Project management
│   │   │   │   ├── webtoons.py    # Webtoon generation
│   │   │   │   ├── panels.py      # Panel management
│   │   │   │   ├── characters.py  # Character management
│   │   │   │   ├── tasks.py       # Task status endpoints
│   │   │   │   └── websocket.py   # WebSocket endpoints
│   │   │   └── router.py          # V1 router aggregation
│   │   └── middleware.py          # API-specific middleware
│   ├── domain/                     # Domain layer (business logic)
│   │   ├── __init__.py
│   │   ├── models/                # Domain models
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # User domain model
│   │   │   ├── project.py        # Project domain model
│   │   │   ├── webtoon.py        # Webtoon domain model
│   │   │   ├── panel.py          # Panel domain model
│   │   │   ├── character.py      # Character domain model
│   │   │   ├── scene.py          # Scene domain model
│   │   │   └── task.py           # Task domain model
│   │   ├── services/              # Domain services
│   │   │   ├── __init__.py
│   │   │   ├── webtoon_service.py # Webtoon business logic
│   │   │   ├── panel_service.py   # Panel business logic
│   │   │   ├── ai_service.py      # AI integration service
│   │   │   ├── auth_service.py    # Authentication service
│   │   │   └── task_service.py    # Task management service
│   │   └── repositories/          # Repository interfaces
│   │       ├── __init__.py
│   │       ├── base.py           # Base repository interface
│   │       ├── user_repository.py
│   │       ├── project_repository.py
│   │       ├── webtoon_repository.py
│   │       ├── panel_repository.py
│   │       └── task_repository.py
│   ├── infrastructure/             # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── database/              # Database implementation
│   │   │   ├── __init__.py
│   │   │   ├── models/           # SQLAlchemy models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── project.py
│   │   │   │   ├── webtoon.py
│   │   │   │   ├── panel.py
│   │   │   │   ├── character.py
│   │   │   │   └── task.py
│   │   │   └── repositories/     # Repository implementations
│   │   │       ├── __init__.py
│   │   │       ├── user_repository.py
│   │   │       ├── project_repository.py
│   │   │       ├── webtoon_repository.py
│   │   │       ├── panel_repository.py
│   │   │       └── task_repository.py
│   │   ├── ai/                    # AI integration
│   │   │   ├── __init__.py
│   │   │   ├── llm/              # Language model integration
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py       # Base LLM interface
│   │   │   │   ├── openai_client.py
│   │   │   │   └── anthropic_client.py
│   │   │   ├── image/            # Image generation
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py       # Base image generator
│   │   │   │   ├── stability_ai.py
│   │   │   │   └── midjourney.py
│   │   │   └── processors/       # AI processing pipelines
│   │   │       ├── __init__.py
│   │   │       ├── story_processor.py
│   │   │       ├── scene_processor.py
│   │   │       └── panel_processor.py
│   │   ├── cache/                 # Caching layer
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py
│   │   │   └── cache_service.py
│   │   ├── storage/               # File storage
│   │   │   ├── __init__.py
│   │   │   ├── local_storage.py
│   │   │   └── s3_storage.py
│   │   └── monitoring/            # Monitoring and observability
│   │       ├── __init__.py
│   │       ├── metrics.py
│   │       ├── tracing.py
│   │       └── health.py
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── webtoon_tasks.py       # Webtoon generation tasks
│   │   ├── image_tasks.py         # Image generation tasks
│   │   ├── ai_tasks.py            # AI processing tasks
│   │   └── cleanup_tasks.py       # Cleanup and maintenance
│   ├── schemas/                    # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py               # Base schemas
│   │   ├── auth.py               # Authentication schemas
│   │   ├── user.py               # User schemas
│   │   ├── project.py            # Project schemas
│   │   ├── webtoon.py            # Webtoon schemas
│   │   ├── panel.py              # Panel schemas
│   │   ├── character.py          # Character schemas
│   │   ├── scene.py              # Scene schemas
│   │   └── task.py               # Task schemas
│   ├── utils/                      # Utilities
│   │   ├── __init__.py
│   │   ├── constants.py          # Application constants
│   │   ├── helpers.py            # Helper functions
│   │   ├── validators.py         # Custom validators
│   │   └── formatters.py         # Data formatters
│   └── tests/                      # Test suite
│       ├── __init__.py
│       ├── conftest.py           # Test configuration
│       ├── unit/                 # Unit tests
│       │   ├── __init__.py
│       │   ├── test_services/
│       │   ├── test_repositories/
│       │   └── test_ai/
│       ├── integration/          # Integration tests
│       │   ├── __init__.py
│       │   ├── test_api/
│       │   ├── test_database/
│       │   └── test_tasks/
│       └── e2e/                  # End-to-end tests
│           ├── __init__.py
│           └── test_webtoon_flow.py
├── docker/                         # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
├── deployment/                     # Deployment configuration
│   ├── kubernetes/
│   │   ├── api-deployment.yaml
│   │   ├── celery-deployment.yaml
│   │   ├── redis-deployment.yaml
│   │   └── mysql-deployment.yaml
│   └── helm/
│       └── sketchdojo/
├── monitoring/                     # Monitoring configuration
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── jaeger/
│       └── jaeger.yml
├── scripts/                        # Utility scripts
│   ├── init_db.py               # Database initialization
│   ├── seed_data.py             # Seed development data
│   ├── migrate.py               # Database migrations
│   └── deploy.sh                # Deployment script
├── requirements/                   # Python dependencies
│   ├── base.txt                 # Base requirements
│   ├── dev.txt                  # Development requirements
│   ├── prod.txt                 # Production requirements
│   └── test.txt                 # Testing requirements
├── .env.example                    # Environment variables template
├── .gitignore
├── README.md
├── pyproject.toml                  # Python project configuration
└── alembic.ini                     # Database migration configuration
```

## Key Architecture Principles

### 1. Clean Architecture Layers
- **API Layer**: FastAPI endpoints and middleware
- **Domain Layer**: Business logic and domain models
- **Infrastructure Layer**: External services and database

### 2. Domain-Driven Design
- Clear domain models with business logic
- Repository pattern for data access
- Service layer for complex business operations

### 3. Async-First Design
- All database operations are async
- Celery for background tasks
- WebSocket for real-time updates

### 4. Observability
- Structured logging with correlation IDs
- Prometheus metrics
- Distributed tracing with Jaeger

### 5. Scalability
- Horizontal scaling with Docker/Kubernetes
- Redis for caching and session management
- Celery for distributed task processing
