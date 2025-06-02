# README.md
# SketchDojo Backend

🎨 **AI-powered webtoon creation platform backend** built with modern Python architecture.

## Overview

SketchDojo enables users to create professional-quality webtoons without drawing skills by leveraging conversational AI. Users describe scenes, characters, and plotlines in natural language, and the platform generates visually compelling webtoon panels optimized for the medium.

## ✨ Features

- 🤖 **AI-Powered Generation**: GPT-4o-mini for story/scene generation, Stability AI for images
- 🎨 **Multiple Art Styles**: Manga, Webtoon, Comic, Anime, and more
- ⚡ **Real-time Updates**: WebSocket-based progress tracking
- 🔄 **Async Processing**: Celery-based background task processing
- 📊 **Observability**: Prometheus metrics, Grafana dashboards, structured logging
- 🐳 **Containerized**: Full Docker deployment with monitoring stack
- 🧪 **Test Coverage**: Comprehensive unit and integration tests
- 🏗️ **Clean Architecture**: Domain-driven design with clear separation of concerns

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   WebSocket     │    │   Monitoring    │
│   (React/Vue)   │◄──►│   Real-time     │    │   (Grafana)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   API Layer    │  Domain Layer   │     Infrastructure         │
│   - Routes     │  - Entities     │     - AI Providers         │
│   - Schemas    │  - Value Objs   │     - Image Generation     │
│   - Middleware │  - Repositories │     - Storage              │
└─────────────────┴─────────────────┴─────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │  Celery Workers │    │   File Storage  │
│   (Cache/Queue) │    │  (Background)   │    │   (Static)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key
- Stability AI API key (optional, will use placeholders if not provided)

### 1. Clone and Setup

```bash
git clone https://github.com/sketchdojo/backend.git
cd sketchdojo-backend

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=your-openai-api-key-here
STABILITY_API_KEY=your-stability-api-key-here  # Optional
SECRET_KEY=your-secret-key-here
```

### 2. Start Development Environment

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start all services
./scripts/start_development.sh
```

This will start:
- 🌐 **API Server**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs
- 📊 **Prometheus**: http://localhost:9090
- 📈 **Grafana**: http://localhost:3000 (admin/admin)
- 💾 **Redis**: localhost:6379

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Generate a webtoon (synchronous test endpoint)
curl "http://localhost:8000/api/v1/generation/sync-test?prompt=A%20brave%20hero%20saves%20the%20world&num_panels=4"
```

## 📁 Project Structure

```
sketchdojo-backend/
├── app/                          # Application code
│   ├── api/                      # API layer (FastAPI routes)
│   ├── application/              # Application services & DTOs
│   ├── domain/                   # Domain entities & business logic
│   ├── infrastructure/           # External integrations
│   ├── tasks/                    # Celery background tasks
│   ├── websocket/                # WebSocket handlers
│   ├── schemas/                  # Pydantic API schemas
│   ├── monitoring/               # Observability components
│   └── utils/                    # Utilities & helpers
├── docker/                       # Docker configuration
├── scripts/                      # Utility scripts
├── tests/                        # Test suite
├── monitoring/                   # Monitoring configs
└── requirements/                 # Python dependencies
```

## 🛠️ Development

### Running Tests

```bash
./scripts/run_tests.sh
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint
flake8 app/
mypy app/
```

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements/development.txt

# Start Redis
redis-server

# Start API server
uvicorn app.main:app --reload --port 8000

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

## 🎯 API Usage Examples

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Subscribe to task updates
ws.send(JSON.stringify({
    type: 'subscribe_task',
    task_id: 'your-task-id-here'
}));
```

### Generation API

```python
import requests

# Start webtoon generation
response = requests.post('http://localhost:8000/api/v1/generation/webtoon', json={
    "prompt": "A cyberpunk detective story with a female protagonist",
    "art_style": "webtoon",
    "num_panels": 6,
    "character_descriptions": ["Detective with neon city background"],
    "additional_context": "Dark, moody atmosphere with futuristic elements"
})

task_id = response.json()['task_id']

# Check task status
status = requests.get(f'http://localhost:8000/api/v1/tasks/{task_id}')
print(status.json())
```

## 📊 Monitoring

### Metrics Available

- **Request Metrics**: Rate, duration, error count
- **Generation Metrics**: Task completion, duration by type
- **WebSocket Metrics**: Active connections, message count
- **AI Provider Metrics**: Request latency, success rate
- **System Metrics**: Memory, CPU via Docker stats

### Grafana Dashboards

Pre-configured dashboards available at http://localhost:3000:

- **API Overview**: Request rates, response times, error rates
- **Generation Pipeline**: Task metrics, completion rates
- **System Health**: Resource usage, service status

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests only
pytest tests/ -m "not slow"    # Skip slow tests
```

## 🚀 Deployment

### Production Deployment

```bash
# Build and deploy
./scripts/deploy.sh

# Or manually with Docker Compose
docker-compose -f docker/docker-compose.yml up -d
```

### Environment Variables

Key environment variables for production:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secure-secret-key

# Optional but recommended
STABILITY_API_KEY=your-stability-api-key
REDIS_URL=redis://your-redis-host:6379/0
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `./scripts/run_tests.sh`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📋 Roadmap

- [ ] **User Authentication & Authorization**
- [ ] **Database Integration** (PostgreSQL)
- [ ] **Advanced Image Editing** capabilities
- [ ] **Team Collaboration** features
- [ ] **Export Formats** (PDF, EPUB, etc.)
- [ ] **Advanced AI Models** integration
- [ ] **Rate Limiting** and quotas
- [ ] **Analytics Dashboard**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 **Email**: support@sketchdojo.com
- 💬 **Discord**: [Join our community](https://discord.gg/sketchdojo)
- 🐛 **Issues**: [GitHub Issues](https://github.com/sketchdojo/backend/issues)
- 📖 **Documentation**: [docs.sketchdojo.com](https://docs.sketchdojo.com)

---

**Built with ❤️ by the SketchDojo Team**
