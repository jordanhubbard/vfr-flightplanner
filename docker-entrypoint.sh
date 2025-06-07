#!/bin/bash
# Docker entrypoint script for Weather Forecasts application

set -e

# Default port
PORT=${PORT:-5060}

# Print environment information
echo "Starting Weather Forecasts application..."
echo "Environment: ${FLASK_ENV:-production}"
echo "Port: ${PORT}"

# Check if API key is set
if [ -z "${OPENWEATHERMAP_API_KEY}" ]; then
    echo "WARNING: OPENWEATHERMAP_API_KEY environment variable is not set."
    echo "Weather overlay features will be limited."
fi

# Run gunicorn with specified port
exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60 "app:create_app()"
