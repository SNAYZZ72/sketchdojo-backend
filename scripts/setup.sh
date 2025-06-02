#!/bin/bash
# Setup script for SketchDojo backend

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

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_status "Creating virtual environment..."
    python -m venv .venv
    print_status "Virtual environment created in .venv directory"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p storage/webtoons storage/panels storage/temp logs

# Generate .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat << EOF > .env
# SketchDojo Environment Variables
# Replace with your actual values

# Security
SECRET_KEY=development_secret_key_replace_in_production
JWT_SECRET=development_jwt_secret_replace_in_production

# API Settings
ENVIRONMENT=development
DEBUG=true

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
STABILITY_API_KEY=your_stability_api_key_here

# Database and Cache
DATABASE_URL=sqlite:///./sketchdojo.db
REDIS_URL=redis://localhost:6379/0
EOF
    print_warning "Created .env file with placeholder values. Please update with your actual API keys."
fi

# Set up pre-commit hooks
print_status "Setting up pre-commit hooks..."
pre-commit install

print_status "Setup completed successfully!"
print_status "Activate the virtual environment with: source .venv/bin/activate"
print_status "Start the development server with: ./scripts/run.sh"
