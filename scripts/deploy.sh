# =============================================================================
# scripts/deploy.sh
# =============================================================================
#!/bin/bash

# SketchDojo Deployment Script

set -e

# Configuration
ENVIRONMENT=${1:-development}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-sketchdojo}
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "🚀 Starting SketchDojo deployment for environment: $ENVIRONMENT"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

# Build images
echo "🔨 Building Docker images..."
docker build -t $DOCKER_REGISTRY/api:$IMAGE_TAG -f docker/Dockerfile .

# Deploy based on environment
case $ENVIRONMENT in
    "development")
        echo "🧪 Deploying to development environment..."
        docker-compose -f docker/docker-compose.dev.yml down
        docker-compose -f docker/docker-compose.dev.yml up -d
        ;;
    "production")
        echo "🌟 Deploying to production environment..."
        docker-compose -f docker/docker-compose.yml down
        docker-compose -f docker/docker-compose.yml up -d
        ;;
    "kubernetes")
        echo "☸️ Deploying to Kubernetes..."
        if ! command_exists kubectl; then
            echo "❌ kubectl is not installed"
            exit 1
        fi
        
        # Apply Kubernetes manifests
        kubectl apply -f deployment/kubernetes/namespace.yaml
        kubectl apply -f deployment/kubernetes/
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "Valid options: development, production, kubernetes"
        exit 1
        ;;
esac

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health check
echo "🏥 Performing health check..."
if [ "$ENVIRONMENT" != "kubernetes" ]; then
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API is healthy"
    else
        echo "❌ API health check failed"
        exit 1
    fi
fi

echo "🎉 Deployment completed successfully!"

# Show useful information
echo ""
echo "📚 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  API docs: http://localhost:8000/docs"
echo "  Grafana: http://localhost:3000 (admin/admin)"
echo "  Prometheus: http://localhost:9090"

