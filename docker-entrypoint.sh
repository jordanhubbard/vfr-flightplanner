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

# Use absolute path for OurAirports CSV
AIRPORTS_CSV="/app/xctry-planner/backend/airports.csv"

# Update airport cache on container startup
python3 /app/scripts/update_airport_cache.py

# Fetch OurAirports CSV if missing (Python-based, robust)
if [ ! -f "$AIRPORTS_CSV" ]; then
  python3 /app/scripts/fetch_ourairports_csv.py
fi

# Debug: List the OurAirports CSV file (if present)
ls -l "$AIRPORTS_CSV" || true

# Merge with OurAirports CSV for full coverage
python3 /app/scripts/merge_airport_datasets.py

# Run gunicorn with specified port
exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60 "app:create_app()"
