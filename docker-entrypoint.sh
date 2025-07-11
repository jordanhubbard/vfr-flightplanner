#!/bin/bash
# Docker entrypoint script for VFR Flight Planner FastAPI application

set -e

# Default configuration
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
ENVIRONMENT=${ENVIRONMENT:-production}

# Print environment information
echo "Starting VFR Flight Planner FastAPI application..."
echo "Environment: ${ENVIRONMENT}"
echo "Host: ${HOST}"
echo "Port: ${PORT}"

# Check if API key is set
if [ -z "${OPENWEATHERMAP_API_KEY}" ]; then
    echo "WARNING: OPENWEATHERMAP_API_KEY environment variable is not set."
    echo "Weather overlay features will be limited."
fi

# Use absolute path for airport cache
AIRPORT_CACHE="/app/app/models/airports_cache.json"
AIRPORTS_CSV="/app/xctry-planner/backend/airports.csv"

# Only update airport cache if it doesn't exist or is empty
if [ ! -f "$AIRPORT_CACHE" ] || [ ! -s "$AIRPORT_CACHE" ]; then
    echo "Airport cache missing or empty. Downloading airport data..."
    python3 /app/scripts/update_airport_cache.py
    
    # Fetch OurAirports CSV if missing (Python-based, robust)
    if [ ! -f "$AIRPORTS_CSV" ]; then
        python3 /app/scripts/fetch_ourairports_csv.py
    fi
    
    # Merge with OurAirports CSV for full coverage
    python3 /app/scripts/merge_airport_datasets.py
else
    echo "Airport cache exists with $(wc -l < "$AIRPORT_CACHE" 2>/dev/null || echo "unknown") entries. Skipping download."
    echo "Use the refresh button in the UI to update airport data."
fi

# Set uvicorn configuration based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    # Development mode with auto-reload
    echo "Running in development mode with auto-reload..."
    exec uvicorn app:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level debug
else
    # Production mode with multiple workers
    echo "Running in production mode with multiple workers..."
    exec uvicorn app:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers 2 \
        --log-level info \
        --access-log \
        --use-colors \
        --proxy-headers \
        --forwarded-allow-ips="*"
fi
