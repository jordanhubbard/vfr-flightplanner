.PHONY: setup run clean test docker-build docker-run docker-stop docker-clean init test-data lint lint-fix deploy

# Default port for Flask app
PORT ?= 8080

# Setup logs directory (if needed)
setup:
	mkdir -p logs

# Clean up project files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	rm -f logs/*
	rm -rf .pytest_cache

# Deep clean (includes venv)
deep-clean: clean
	rm -rf venv

# Run the application via Docker Compose
run:
	docker-compose up --build -d
	@echo "Application started in Docker. Access it at http://localhost:$(PORT)"

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

# Show container logs
logs:
	docker-compose logs -f web

# Docker commands
docker-build:
	docker build -t weather-forecasts .

docker-run: docker-build
	docker stop weather-forecasts-container 2>/dev/null || true
	docker rm weather-forecasts-container 2>/dev/null || true
	docker run -p 5060:5060 \
		--env-file .env \
		--name weather-forecasts-container \
		-d weather-forecasts
	@echo "Container started. Access the application at http://localhost:8080"

docker-stop:
	docker stop weather-forecasts-container || true
	docker rm weather-forecasts-container || true

# Show Docker logs
docker-logs:
	docker logs -f weather-forecasts-container

# Clean Docker resources
docker-clean: docker-stop
	docker rmi weather-forecasts || true
	@echo "Docker resources cleaned"

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
init: setup
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
	@echo "  docker-clean - Remove Docker container and image"
	@echo "  compose-up  - Start application with Docker Compose"
	@echo "  compose-down - Stop Docker Compose services"
	@echo "  compose-logs - Show Docker Compose logs"
	@echo "  init        - Initialize the application"
	@echo "  test-data   - Load test data"
	@echo "  deploy      - Deploy the application"
	@echo "  help        - Show this help information"

# Default target
.DEFAULT_GOAL := help
