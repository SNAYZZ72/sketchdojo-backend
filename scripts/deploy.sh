#!/bin/bash
# Deployment script for SketchDojo backend

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function for status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

# Helper function for warnings
print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Helper function for errors
print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY environment variable is not set"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for stability API key
if [ -z "$STABILITY_API_KEY" ]; then
    print_warning "STABILITY_API_KEY environment variable is not set"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests before deployment
print_status "Running tests before deployment..."
./scripts/run_tests.sh

# Build Docker images
print_status "Building Docker images..."
docker build -t sketchdojo-api:latest -f docker/Dockerfile .
docker build -t sketchdojo-worker:latest -f docker/Dockerfile.worker .

# Tag images with version
VERSION=$(git describe --tags --always)
docker tag sketchdojo-api:latest sketchdojo-api:$VERSION
docker tag sketchdojo-worker:latest sketchdojo-worker:$VERSION

# Push to container registry (if applicable)
if [ -n "$CONTAINER_REGISTRY" ]; then
    print_status "Pushing to container registry..."
    docker tag sketchdojo-api:latest $CONTAINER_REGISTRY/sketchdojo-api:latest
    docker tag sketchdojo-api:$VERSION $CONTAINER_REGISTRY/sketchdojo-api:$VERSION
    docker tag sketchdojo-worker:latest $CONTAINER_REGISTRY/sketchdojo-worker:latest
    docker tag sketchdojo-worker:$VERSION $CONTAINER_REGISTRY/sketchdojo-worker:$VERSION

    docker push $CONTAINER_REGISTRY/sketchdojo-api:latest
    docker push $CONTAINER_REGISTRY/sketchdojo-api:$VERSION
    docker push $CONTAINER_REGISTRY/sketchdojo-worker:latest
    docker push $CONTAINER_REGISTRY/sketchdojo-worker:$VERSION
fi

# Deploy to environment
print_status "Deploying to environment..."
if [ "$DEPLOY_ENV" = "production" ]; then
    print_status "Deploying to production..."
    # Add production deployment commands
    # e.g., kubectl apply, docker-compose on remote, etc.
else
    print_status "Deploying to development/staging..."
    # Add staging deployment commands
    docker-compose -f docker/docker-compose.yml up -d
fi

print_status "Deployment completed successfully!"
