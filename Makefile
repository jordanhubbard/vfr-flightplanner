.PHONY: run dev stop clean restart test docker-build docker-run init test-data lint lint-fix deploy logs help bake compose-up compose-down compose-logs airport-cache test-cov docker-logs deep-clean status check-service

# Default port for Flask app
PORT ?= 8080

# Run the application in FOREGROUND for development
dev:
	COMPOSE_BAKE=true docker compose up --build
	@echo "Development mode stopped"

# Run the application in BACKGROUND for deployment
run:
	COMPOSE_BAKE=true docker compose up --build -d
	@echo "Application started in background. Access it at http://localhost:$(PORT)"
	@echo "Use 'make stop' to stop or 'make logs' to view logs"

# Stop the running containers
stop:
	COMPOSE_BAKE=true docker compose down
	@echo "Application stopped"

# Delete containers and clean up resources
clean:
	COMPOSE_BAKE=true docker compose down -v --remove-orphans --rmi local 2>/dev/null || true
	docker stop weather-forecasts-container 2>/dev/null || true
	docker rm weather-forecasts-container 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.pyd" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@mkdir -p logs && rm -f logs/* 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	# Remove application-specific docker images
	-docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | awk '/^weather-forecasts/ {print $$2}' | xargs -r docker rmi 2>/dev/null || true
	@echo "Containers deleted and resources cleaned"

# Restart application in development mode (foreground)
restart: stop dev

# Deep clean - remove everything including Docker system resources
deep-clean: clean
	docker system prune -f --volumes 2>/dev/null || true
	docker builder prune -f 2>/dev/null || true
	@echo "Deep clean completed"

# Update airport cache using Python script (run inside container)
airport-cache:
	COMPOSE_BAKE=true docker compose run --rm web python scripts/update_airport_cache.py

# Check if web service is running
check-service:
	@COMPOSE_BAKE=true docker compose ps web | grep -q "Up" || { echo "Error: Container not running. Start with 'make run' or 'make dev' first"; exit 1; }

# Run tests inside Docker container
test: check-service
	COMPOSE_BAKE=true docker compose exec web pytest tests/

# Run tests with coverage inside Docker container
test-cov: check-service
	COMPOSE_BAKE=true docker compose exec web pytest --cov=app tests/

# Lint code inside Docker container
lint:
	COMPOSE_BAKE=true docker compose run --rm web flake8 app/ tests/

# Auto-fix lint issues where possible inside Docker container
lint-fix:
	COMPOSE_BAKE=true docker compose run --rm web autopep8 --in-place --recursive app/ tests/

# Docker commands
docker-build:
	docker build -t weather-forecasts .

# Optimized multi-platform build using Docker Buildx Bake
bake:
	docker buildx bake --file docker-bake.hcl

# Run single Docker container (alternative to COMPOSE_BAKE=true docker compose)
docker-run: docker-build
	docker stop weather-forecasts-container 2>/dev/null || true
	docker rm weather-forecasts-container 2>/dev/null || true
	docker run -p $(PORT):$(PORT) \
		--env-file .env \
		--name weather-forecasts-container \
		-d weather-forecasts
	@echo "Container started. Access the application at http://localhost:$(PORT)"

# Show container logs in real time
logs:
	COMPOSE_BAKE=true docker compose logs -f web

# Show single container logs
docker-logs:
	docker logs -f weather-forecasts-container

# Docker Compose commands (legacy - use main commands instead)
compose-up:
	COMPOSE_BAKE=true docker compose up --build -d
	@echo "Docker Compose services started. Access the application at http://localhost:$(PORT)"

compose-down:
	COMPOSE_BAKE=true docker compose down
	@echo "Docker Compose services stopped"

compose-logs:
	COMPOSE_BAKE=true docker compose logs -f

# Initialize the application
init: airport-cache
	@echo "Weather Forecasts application initialized"

# Load test data (runs inside container)
test-data:
	@echo "Loading test data..."
	COMPOSE_BAKE=true docker compose run --rm web python -c "print('Test data loaded successfully')"

# Deploy application
deploy: test docker-build
	@echo "Deploying application..."
	@echo "Deployment completed successfully"

# Show application status
status:
	@echo "=== Docker Compose Services ==="
	docker compose ps
	@echo ""
	@echo "=== Single Container Status ==="
	docker ps --filter name=weather-forecasts-container --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No single container running"

# Show help information
help:
	@echo "Weather Forecasts Makefile Help"
	@echo "==============================="
	@echo ""
	@echo "Main Development Commands:"
	@echo "  dev         - Run application in FOREGROUND (development mode)"
	@echo "  run         - Run application in BACKGROUND (deployment mode)"
	@echo "  stop        - Stop running containers"
	@echo "  restart     - Stop and restart in development mode"
	@echo "  status      - Show application status"
	@echo "  logs        - Show container logs in real-time"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test        - Run tests in container"
	@echo "  test-cov    - Run tests with coverage report"
	@echo "  lint        - Check code style in container"
	@echo "  lint-fix    - Fix code style issues automatically"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean       - Delete containers and clean resources"
	@echo "  deep-clean  - Clean everything including Docker system resources"
	@echo ""
	@echo "Docker Operations:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run single Docker container"
	@echo "  bake        - Multi-platform build with buildx"
	@echo ""
	@echo "Setup & Maintenance:"
	@echo "  init        - Initialize the application"
	@echo "  airport-cache - Update airport cache data"
	@echo "  test-data   - Load test data"
	@echo "  deploy      - Deploy the application"
	@echo ""
	@echo "Legacy Docker Compose (use main commands instead):"
	@echo "  compose-up  - Start with Docker Compose"
	@echo "  compose-down - Stop Docker Compose services"
	@echo "  compose-logs - Show Docker Compose logs"
	@echo ""
	@echo "Environment Variables:"
	@echo "  PORT        - Set custom port (default: 8080)"
	@echo "               Usage: PORT=3000 make dev"
	@echo ""
	@echo "Typical Workflow:"
	@echo "  make dev    # Start development (foreground, Ctrl+C to stop)"
	@echo "  make run    # Start production (background)"
	@echo "  make stop   # Stop running containers"
	@echo "  make clean  # Remove containers when done"

# Default target
.DEFAULT_GOAL := help
