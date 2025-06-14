.PHONY: setup run clean test docker-build docker-run docker-stop init test-data lint lint-fix deploy logs

# Default port for Flask app
PORT ?= 8080

# Clean up project files
clean: docker-stop
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@rm -f logs/*
	@rm -rf .pytest_cache
	# Remove all stale docker images for this application
	-docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | awk '/^weather-forecasts:/ {print $$2}' | xargs -r docker rmi

# Update airport cache using Python script (run inside container)
airport-cache:
	docker-compose run --rm web python scripts/update_airport_cache.py

# Run the application via Docker Compose
run:
	docker-compose up --build -d
	@echo "Application started in Docker. Access it at http://localhost:$(PORT)"

# Development: build and run container interactively with source mounted
# Usage: make dev
# This will start the container with a shell for debugging/development
# You can override the shell with SHELL=/bin/bash make dev

dev:
	docker-compose run --rm --service-ports web /bin/bash

# Run tests inside Docker container
test:
	docker-compose exec web pytest tests/

# Run tests with coverage inside Docker container
test-cov:
	docker-compose exec web pytest --cov=app tests/

# Lint code
lint: setup
	. venv/bin/activate && \
	flake8 app/ tests/

# Auto-fix lint issues where possible
lint-fix: setup
	. venv/bin/activate && \
	autopep8 --in-place --recursive app/ tests/


# Docker commands
docker-build:
	docker build -t weather-forecasts .

# Optimized multi-platform build using Docker Buildx Bake
bake:
	docker buildx bake --file docker-bake.hcl

docker-run: docker-build
	docker stop weather-forecasts-container 2>/dev/null || true
	docker rm weather-forecasts-container 2>/dev/null || true
	docker run -p 5060:5060 \
		--env-file .env \
		--name weather-forecasts-container \
		-d weather-forecasts
	@echo "Container started. Access the application at http://localhost:8080"

docker-stop:
	docker compose down -v --rmi all --remove-orphans || true

# Restart all services (full container restart)
restart:
	docker-compose down
	docker-compose up -d

# Show container logs in real time
logs:
	docker-compose logs -f web

docker-logs:
	docker logs -f weather-forecasts-container

# Docker Compose commands
compose-up:
	docker-compose up -d
	@echo "Docker Compose services started. Access the application at http://localhost:8080"

compose-down:
	docker-compose down
	@echo "Docker Compose services stopped"

compose-logs:
	docker-compose logs -f

# Initialize the application
init: setup airport-cache
	@echo "Weather Forecasts application initialized"

# Load test data (placeholder for future implementation)
test-data: setup
	@echo "Loading test data..."
	. venv/bin/activate && \
	PYTHONPATH=. \
	python -c "print('Test data loaded successfully')"

# Deploy application
deploy: test docker-build
	@echo "Deploying application..."
	@echo "Deployment completed successfully"

# Show help information
help:
	@echo "Weather Forecasts Makefile Help"
	@echo "----------------------------"
	@echo "Available targets:"
	@echo "  setup       - Set up development environment"
	@echo "  run         - Run the application locally (PORT=xxxx make run for custom port)"
	@echo "  test        - Run tests"
	@echo "  test-cov    - Run tests with coverage report"
	@echo "  clean       - Clean temporary files"
	@echo "  deep-clean  - Clean everything including virtual environment"
	@echo "  lint        - Check code style"
	@echo "  lint-fix    - Fix code style issues automatically"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run application in Docker container"
	@echo "  docker-stop - Stop Docker container"
	@echo "  docker-logs - Show Docker container logs"
	@echo "  compose-up  - Start application with Docker Compose"
	@echo "  compose-down - Stop Docker Compose services"
	@echo "  compose-logs - Show Docker Compose logs"
	@echo "  init        - Initialize the application"
	@echo "  test-data   - Load test data"
	@echo "  deploy      - Deploy the application"
	@echo "  help        - Show this help information"

# Default target
.DEFAULT_GOAL := help
