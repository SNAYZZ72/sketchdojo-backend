#!/bin/bash
# Linting script for SketchDojo backend

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

# Parse arguments
FIX=0
if [ "$1" = "--fix" ]; then
    FIX=1
fi

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

# Run flake8
print_status "Running flake8..."
flake8 app tests

# Run mypy
print_status "Running mypy type checking..."
mypy app

# Run isort check
print_status "Checking import order with isort..."
if [ $FIX -eq 1 ]; then
    isort app tests
else
    isort --check-only app tests
fi

# Run black
print_status "Checking code formatting with black..."
if [ $FIX -eq 1 ]; then
    black app tests
else
    black --check app tests
fi

print_status "Linting completed successfully!"
