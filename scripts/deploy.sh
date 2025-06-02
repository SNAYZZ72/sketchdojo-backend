# scripts/deploy.sh
#!/bin/bash

set -e

echo "🚀 Deploying SketchDojo to Production"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if we're on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    print_error "Deployment must be done from main branch. Current branch: $BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    print_error "Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Run tests before deployment
print_status "Running tests before deployment..."
./scripts/run_tests.sh

# Build Docker images
print_status "Building Docker images..."
docker build -t sketchdojo-api:latest -f docker/Dockerfile.api .
docker build -t sketchdojo-worker:latest -f docker/Dockerfile.worker .

# Tag images with version
VERSION=$(git describe --tags --always)
docker tag sketchdojo-api:latest sketchdojo-api:$VERSION
docker tag sketchdojo-worker:latest sketchdojo-worker:$VERSION

print_status "Built images with version: $VERSION"

# Here you would typically push to a container registry
# docker push sketchdojo-api:$VERSION
# docker push sketchdojo-worker:$VERSION

print_status "🎉 Deployment preparation completed!"
print_warning "Remember to:"
echo "  1. Push images to your container registry"
echo "  2. Update your production environment"
echo "  3. Run database migrations if needed"
echo "  4. Monitor the deployment"

# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sketchdojo-backend"
version = "2.0.0"
description = "AI-powered webtoon creation platform backend"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "SketchDojo Team", email = "team@sketchdojo.com"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Framework :: FastAPI",
    "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    "Topic :: Multimedia :: Graphics",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.0.3",
    "redis>=5.0.1",
    "celery>=5.3.4",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "httpx>=0.25.2",
    "aiofiles>=23.2.1",
    "pillow>=10.1.0",
    "openai>=1.3.7",
    "prometheus-client>=0.19.0",
    "structlog>=23.2.0",
    "websockets>=12.0",
    "tenacity>=8.2.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "black>=23.11.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.7.1",
    "pre-commit>=3.5.0",
]
prod = [
    "gunicorn>=21.2.0",
]

[project.urls]
Homepage = "https://github.com/sketchdojo/backend"
Documentation = "https://docs.sketchdojo.com"
Repository = "https://github.com/sketchdojo/backend"
"Bug Tracker" = "https://github.com/sketchdojo/backend/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 100
known_first_party = ["app"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
