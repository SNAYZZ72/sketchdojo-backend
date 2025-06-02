#!/bin/bash
# Test runner script for SketchDojo backend

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

# Default values
COVERAGE=0
VERBOSE=0
E2E=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--coverage)
            COVERAGE=1
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -e|--e2e)
            E2E=1
            shift
            ;;
        *)
            # Unknown option
            shift
            ;;
    esac
done

# Ensure virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_status "Activating virtual environment..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}ERROR:${NC} Virtual environment not found. Please create and activate it first."
        exit 1
    fi
fi

# Set environment variables for testing
export ENVIRONMENT=test
export SKETCHDOJO_SETTINGS_MODULE=app.config

# Run unit tests
if [ $VERBOSE -eq 1 ]; then
    PYTEST_ARGS="-v"
else
    PYTEST_ARGS=""
fi

if [ $COVERAGE -eq 1 ]; then
    print_status "Running tests with coverage..."
    python -m pytest tests/unit $PYTEST_ARGS --cov=app --cov-report=term-missing
else
    print_status "Running unit tests..."
    python -m pytest tests/unit $PYTEST_ARGS
fi

# Run integration tests
print_status "Running integration tests..."
python -m pytest tests/integration $PYTEST_ARGS

# Run E2E tests if requested
if [ $E2E -eq 1 ]; then
    print_status "Running end-to-end tests..."
    python -m pytest tests/e2e $PYTEST_ARGS
fi

print_status "All tests completed successfully!"
