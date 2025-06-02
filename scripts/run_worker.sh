#!/bin/bash
# Run worker process for SketchDojo backend

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

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING:${NC} .env file not found. Creating a default one."
    ./scripts/setup.sh
fi

# Export environment variables
export ENVIRONMENT=development
export DEBUG=true

# Run the worker
print_status "Starting SketchDojo background worker..."
python -m app.worker.main
