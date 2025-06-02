# scripts/run_tests.sh
#!/bin/bash

set -e

echo "🧪 Running SketchDojo Test Suite"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Set up test environment
export ENVIRONMENT=test
export REDIS_URL=redis://localhost:6379/15  # Use different DB for tests

# Install test dependencies
print_status "Installing test dependencies..."
pip install -r requirements/development.txt

# Run linting
print_status "Running code linting..."
echo "🔍 Running flake8..."
flake8 app/ --max-line-length=100 --ignore=E203,W503

echo "🔍 Running mypy..."
mypy app/ --ignore-missing-imports

echo "🔍 Running black (check only)..."
black --check app/

echo "🔍 Running isort (check only)..."
isort --check-only app/

# Run tests
print_status "Running tests..."
pytest tests/ -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=80

print_status "✅ All tests completed!"
echo "📊 Coverage report available at htmlcov/index.html"
