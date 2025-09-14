#!/bin/bash
set -e

# VFR Flight Planner - Docker Entrypoint Script

echo "🚀 Starting VFR Flight Planner Application..."

# Set default environment if not provided
export ENVIRONMENT=${ENVIRONMENT:-development}
export PORT=${PORT:-8080}
export HOST=${HOST:-0.0.0.0}

echo "Environment: $ENVIRONMENT"
echo "Port: $PORT"
echo "Host: $HOST"

# Function to start the FastAPI application
start_fastapi() {
    echo "🐍 Starting FastAPI backend on $HOST:$PORT..."
    cd /app
    if [ "$ENVIRONMENT" = "development" ]; then
        exec uvicorn app:app --host $HOST --port $PORT --reload --log-level info
    else
        exec uvicorn app:app --host $HOST --port $PORT --log-level info
    fi
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    cd /app
    exec pytest tests/ -v --cov=app --cov-report=html --cov-report=term
}

# Main execution logic
case "${1:-start}" in
    start)
        start_fastapi
        ;;
    test)
        run_tests
        ;;
    bash|sh)
        exec /bin/bash
        ;;
    *)
        echo "Usage: $0 {start|test|bash}"
        echo "  start - Start the FastAPI application (default)"
        echo "  test  - Run the test suite"
        echo "  bash  - Open a bash shell"
        exit 1
        ;;
esac