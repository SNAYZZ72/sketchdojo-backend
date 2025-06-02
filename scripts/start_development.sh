# scripts/start_development.sh
#!/bin/bash

set -e

echo "🚀 Starting SketchDojo Development Environment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Created .env file. Please edit it with your API keys."
    else
        print_error ".env.example file not found!"
        exit 1
    fi
fi

# Check for required environment variables
source .env
required_vars=("OPENAI_API_KEY" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your-api-key-here" ] || [ "${!var}" = "your-secret-key-here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    print_error "Please set these in your .env file before continuing."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p static/images static/generated_images static/temp logs

# Start services with Docker Compose
print_status "Starting services with Docker Compose..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 10

# Check service health
services=("redis" "api")
for service in "${services[@]}"; do
    print_status "Checking $service health..."
    if docker-compose -f docker/docker-compose.yml ps "$service" | grep -q "healthy\|Up"; then
        print_status "$service is running"
    else
        print_warning "$service might not be ready yet"
    fi
done

# Display service URLs
print_status "🎉 Development environment is ready!"
echo ""
echo "📋 Service URLs:"
echo "  🌐 API: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "  📊 Prometheus: http://localhost:9090"
echo "  📈 Grafana: http://localhost:3000 (admin/admin)"
echo "  💾 Redis: localhost:6379"
echo ""
echo "🔧 Useful Commands:"
echo "  📖 View logs: docker-compose -f docker/docker-compose.yml logs -f"
echo "  🛑 Stop services: docker-compose -f docker/docker-compose.yml down"
echo "  🔄 Restart services: docker-compose -f docker/docker-compose.yml restart"
echo "  🧹 Clean up: docker-compose -f docker/docker-compose.yml down -v"
echo ""
echo "🧪 Test the API:"
echo "  curl http://localhost:8000/health"
