# =============================================================================
# Makefile
# =============================================================================
.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements/dev.txt

dev: ## Install in development mode
	pip install -e . && pre-commit install

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

lint: ## Run linting
	black --check app/ tests/
	isort --check-only app/ tests/
	flake8 app/ tests/
	mypy app/

format: ## Format code
	black app/ tests/
	isort app/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker images
	docker build -t sketchdojo/api:latest -f docker/Dockerfile .

docker-up: ## Start development environment
	docker-compose -f docker/docker-compose.dev.yml up -d

docker-down: ## Stop development environment
	docker-compose -f docker/docker-compose.dev.yml down

docker-logs: ## View logs
	docker-compose -f docker/docker-compose.dev.yml logs -f

deploy-dev: ## Deploy to development
	./scripts/deploy.sh development

deploy-prod: ## Deploy to production
	./scripts/deploy.sh production

init-db: ## Initialize database
	python scripts/init_db.py

