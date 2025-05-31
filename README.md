# =============================================================================
# README.md
# =============================================================================
# SketchDojo Backend

A next-generation AI-powered platform for webtoon creation, built with modern Python technologies and clean architecture principles.

## 🚀 Features

- **AI-Powered Generation**: Create webtoons using state-of-the-art LLMs and image generation
- **Real-time Updates**: WebSocket support for live progress tracking
- **Scalable Architecture**: Microservices-ready with Docker and Kubernetes
- **Background Processing**: Celery-based task queue for heavy operations
- **Comprehensive Monitoring**: Prometheus metrics and Grafana dashboards
- **Clean Architecture**: Domain-driven design with separation of concerns

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │  Celery Worker  │    │     Redis       │
│    (HTTP/WS)    │    │   (AI Tasks)    │    │ (Cache/Broker)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    │    ┌─────────────────┐
         │     MySQL       │    │    │   Monitoring    │
         │   (Database)    │    │    │  (Prometheus)   │
         └─────────────────┘    │    └─────────────────┘
                                │
         ┌─────────────────┐    │
         │   AI Services   │    │
         │ (OpenAI/StabilityAI) │
         └─────────────────┘    │
```

## 🛠️ Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: MySQL with SQLAlchemy (async)
- **Cache**: Redis
- **Task Queue**: Celery
- **AI Integration**: OpenAI GPT-4, Stability AI
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes ready

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- MySQL 8.0+
- Redis 7+

## 🚀 Quick Start

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone https://github.com/sketchdojo/backend.git
   cd sketchdojo-backend
   make install
   make dev
   ```

2. **Environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start services**:
   ```bash
   make docker-up
   ```

4. **Initialize database**:
   ```bash
   make init-db
   ```

5. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Grafana Dashboard: http://localhost:3000 (admin/admin)
   - Prometheus Metrics: http://localhost:9090

### Production Deployment

1. **Using Docker Compose**:
   ```bash
   make deploy-prod
   ```

2. **Using Kubernetes**:
   ```bash
   ./scripts/deploy.sh kubernetes
   ```

## 📚 API Documentation

### Authentication
```bash
# Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "SecurePass123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123"
```

### Webtoon Generation
```bash
# Create project
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Webtoon", "description": "A cool story"}'

# Generate webtoon
curl -X POST "http://localhost:8000/api/v1/webtoons/generate?project_id=PROJECT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"story_prompt": "A hero saves the world", "panel_count": 6}'
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration

# With coverage
pytest --cov=app --cov-report=html
```

## 📊 Monitoring

The platform includes comprehensive monitoring:

- **Health Checks**: `/health` endpoint with detailed service status
- **Metrics**: Prometheus metrics for requests, tasks, and AI operations
- **Tracing**: Jaeger distributed tracing
- **Logging**: Structured JSON logging with correlation IDs

## 🔧 Development

### Code Quality
```bash
make lint    # Check code quality
make format  # Auto-format code
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

### Adding New Features

1. **Domain Model**: Define in `app/domain/models/`
2. **Database Model**: Add to `app/infrastructure/database/models/`
3. **Repository**: Implement in `app/infrastructure/database/repositories/`
4. **Service**: Create business logic in `app/domain/services/`
5. **API**: Add endpoints in `app/api/v1/endpoints/`
6. **Tests**: Add comprehensive tests

## 🚦 Configuration

Key environment variables:

- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for LLM
- `STABILITY_AI_API_KEY`: Stability AI key for image generation
- `SECRET_KEY`: JWT signing secret
- `ENVIRONMENT`: deployment environment (development/production)

## 📈 Performance

- **Async/Await**: Full async support for high concurrency
- **Connection Pooling**: Optimized database connections
- **Caching**: Redis-based caching for frequent operations
- **Background Tasks**: CPU-intensive AI operations in Celery workers
- **Rate Limiting**: Built-in rate limiting middleware

## 🛡️ Security

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt for password security
- **CORS**: Configurable CORS policies
- **Rate Limiting**: Request rate limiting
- **Input Validation**: Pydantic-based validation
- **SQL Injection Protection**: SQLAlchemy ORM

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

- Documentation: https://docs.sketchdojo.com
- Issues: https://github.com/sketchdojo/backend/issues
- Email: support@sketchdojo.com

---

Built with ❤️ by the SketchDojo Team