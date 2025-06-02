.PHONY: help install dev test lint format clean docker-build docker-up docker-down docker-logs docker-clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements/development.txt
	pre-commit install

dev: ## Start development environment
	./scripts/start_development.sh

test: ## Run tests
	./scripts/run_tests.sh

lint: ## Run linting
	flake8 app/
	mypy app/
	black --check app/
	isort --check-only app/

format: ## Format code
	black app/
	isort app/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

docker-build: ## Build Docker images
	docker build -f docker/Dockerfile.api -t sketchdojo-api:latest .
	docker build -f docker/Dockerfile.worker -t sketchdojo-worker:latest .

docker-up: ## Start Docker services
	docker-compose -f docker/docker-compose.yml up -d

docker-down: ## Stop Docker services
	docker-compose -f docker/docker-compose.yml down

docker-logs: ## Show Docker logs
	docker-compose -f docker/docker-compose.yml logs -f

docker-clean: ## Clean Docker resources
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f
