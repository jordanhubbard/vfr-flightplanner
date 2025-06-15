#!/bin/bash
# Docker entrypoint script for Flight Planner application

set -e

# Default port
PORT=${PORT:-8080}

# Print environment information
echo "Starting Flight Planner application..."
echo "Environment: ${FLASK_ENV:-production}"
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

# Run gunicorn with specified port
exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60 "app:create_app()"
