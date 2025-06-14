#!/bin/bash
# Strictly containerized test runner for Weather Forecasts application
set -e

echo "Running tests in Docker container..."
docker-compose exec web pytest tests/

echo "Tests completed in container."
