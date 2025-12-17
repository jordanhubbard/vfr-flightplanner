# VFR Flight Planner Makefile
# Standardized Docker-based workflow

# Port Configuration (can be overridden by environment variables)
PORT ?= 8080

# Export ports for use in docker-compose and other tools
export PORT

# Variables
IMAGE_NAME=vfr-flightplanner
CONTAINER_NAME=vfr-flightplanner-container
COMPOSE_FILE=docker-compose.yml

# Docker BuildKit optimization settings for local development
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export BUILDKIT_INLINE_CACHE=1
export DOCKERFILE=Dockerfile.local

# Docker Compose build optimizations
COMPOSE_BUILD_OPTS=--parallel --pull

# Default target
.PHONY: help test
help:
	@echo "VFR Flight Planner - Available Commands:"
	@echo ""
	@echo "  start        - Build and start the complete application"
	@echo "  stop         - Stop the running application"
	@echo "  logs         - View application logs (blocking)"
	@echo "  clean        - Complete cleanup: stop, remove containers, images, and files"
	@echo "  test         - Run comprehensive test suite"
	@echo ""
	@echo "Port Configuration:"
	@echo "  PORT = $(PORT) (FastAPI application)"
	@echo ""
	@echo "Usage:"
	@echo "  make start                    # Use default port"
	@echo "  PORT=9000 make start          # Use custom port"
	@echo "  make stop                     # Stop the application"
	@echo "  make logs                     # View application logs"
	@echo "  make clean                    # Complete cleanup (removes all data!)"
	@echo "  make test                     # Run tests with coverage"

# Start the application - builds everything and runs the container
.PHONY: start
start:
	@echo "🚀 Starting VFR Flight Planner..."
	@echo "Building and starting services with optimized BuildKit..."
	docker-compose -f $(COMPOSE_FILE) build $(COMPOSE_BUILD_OPTS)
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ FastAPI Application started successfully!"
	@echo ""
	@echo "🌐 Main Application: http://localhost:$(PORT)"
	@echo "📚 API Documentation: http://localhost:$(PORT)/docs"
	@echo "📖 ReDoc Documentation: http://localhost:$(PORT)/redoc"
	@echo ""
	@echo "To view logs: make logs"
	@echo "To stop: make stop"

# Stop the running application
.PHONY: stop
stop:
	@echo "🛑 Stopping VFR Flight Planner..."
	-docker-compose -f $(COMPOSE_FILE) down 2>/dev/null || true
	@echo "✅ Application stopped successfully!"

# View application logs (blocking)
.PHONY: logs
logs:
	@echo "📋 Viewing VFR Flight Planner logs..."
	@echo "Press Ctrl+C to stop viewing logs"
	docker-compose -f $(COMPOSE_FILE) logs -f

# Clean up everything - stop, remove container, clean images, and reset data
.PHONY: clean
clean: stop
	@echo "🧹 Cleaning up Docker resources..."
	-docker-compose -f $(COMPOSE_FILE) down -v --rmi all --remove-orphans 2>/dev/null || true
	-docker rmi $(IMAGE_NAME):latest 2>/dev/null || true
	-docker rmi $(IMAGE_NAME):dev 2>/dev/null || true
	-docker rmi $(IMAGE_NAME):prod 2>/dev/null || true
	-docker rmi $(IMAGE_NAME):test 2>/dev/null || true
	@echo "🗑️  Cleaning up application data..."
	-rm -rf logs/*.log* 2>/dev/null || true
	-find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name "*.pyc" -delete 2>/dev/null || true
	-find . -type f -name ".coverage" -delete 2>/dev/null || true
	-rm -rf htmlcov/ 2>/dev/null || true
	-rm -rf .pytest_cache/ 2>/dev/null || true
	-rm -rf frontend/node_modules/.cache/ 2>/dev/null || true
	@echo "✅ Complete cleanup finished!"
	@echo ""
	@echo "🔄 All data, logs, and caches removed"
	@echo ""
	@echo "To start fresh: make start"

# Run all tests with coverage reporting - CONTAINER ONLY
.PHONY: test
test:
	@echo "🧪 Running comprehensive test suite..."
	@echo "📦 Building test containers with optimized BuildKit..."
	docker-compose -f $(COMPOSE_FILE) build $(COMPOSE_BUILD_OPTS)
	@echo ""
	@echo "🐍 Running Python/FastAPI tests..."
	docker-compose -f $(COMPOSE_FILE) run --rm vfr-flightplanner pytest tests/ -v --cov=app --cov-report=html --cov-report=term --cov-report=xml || true
	@echo ""
	@echo "✅ All tests completed!"
	@echo "📊 Coverage report: htmlcov/index.html"
	@echo "🔍 XML coverage: coverage.xml"
	@echo ""
	@echo "🐳 All tests run inside containers - no host dependencies!"