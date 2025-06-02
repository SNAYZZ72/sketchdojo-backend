#!/bin/bash

set -e

echo "🛠️ Setting up SketchDojo Development Environment"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    print_warning "Python 3.11+ required. Found: $python_version"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

print_status "Python version OK: $python_version"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements/development.txt

# Install pre-commit hooks
print_status "Installing pre-commit hooks..."
pre-commit install

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p static/images static/generated_images static/temp logs

# Set permissions
chmod +x scripts/*.sh

print_status "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'make dev' or './scripts/start_development.sh' to start"
echo "3. Visit http://localhost:8000/docs for API documentation"
