#!/bin/bash
# Run development server for SketchDojo backend

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
HOST="0.0.0.0"
PORT="8000"
RELOAD=1

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --host=*)
            HOST="${key#*=}"
            shift
            ;;
        --port=*)
            PORT="${key#*=}"
            shift
            ;;
        --no-reload)
            RELOAD=0
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

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING:${NC} .env file not found. Creating a default one."
    ./scripts/setup.sh
fi

# Export environment variables
export ENVIRONMENT=development
export DEBUG=true

# Run the server
print_status "Starting SketchDojo API server at $HOST:$PORT..."

if [ $RELOAD -eq 1 ]; then
    RELOAD_ARG="--reload"
else
    RELOAD_ARG=""
fi

uvicorn app.main:app --host $HOST --port $PORT $RELOAD_ARG
