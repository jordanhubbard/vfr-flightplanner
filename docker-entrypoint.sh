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

# Initialize airport cache if not present
initialize_airport_cache() {
    # Use persistent volume for cache
    CACHE_FILE="/app/data/airports_cache.json"
    mkdir -p /app/data
    
    if [ ! -f "$CACHE_FILE" ]; then
        echo "📍 Airport cache not found, initializing..."
        
        # Try OurAirports CSV (free, no API key required)
        if python3 /app/scripts/fetch_ourairports_csv.py; then
            echo "✓ Downloaded OurAirports CSV data"
            
            # Convert CSV to JSON format
            python3 -c "
import csv
import json
import os

csv_path = '/app/xctry-planner/backend/airports.csv'
json_path = '/app/data/airports_cache.json'

if os.path.exists(csv_path):
    airports = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['ident']:
                continue
            airport = {
                'icao': row['ident'] if len(row['ident']) == 4 else None,
                'iata': row['iata_code'] or None,
                'name': row['name'],
                'city': row['municipality'] or '',
                'country': row['iso_country'] or '',
                'latitude': float(row['latitude_deg']) if row['latitude_deg'] else None,
                'longitude': float(row['longitude_deg']) if row['longitude_deg'] else None,
                'elevation': float(row['elevation_ft']) if row['elevation_ft'] else None,
                'type': row['type'] or '',
            }
            airports.append(airport)
    
    with open(json_path, 'w') as f:
        json.dump(airports, f)
    
    print(f'✓ Converted {len(airports)} airports to JSON cache')
else:
    print('✗ CSV file not found')
"
            echo "✓ Airport cache initialized with $(wc -l < "$CACHE_FILE") airports"
        else
            echo "⚠️  Failed to initialize airport cache - airport lookups may not work"
        fi
    else
        CACHE_SIZE=$(wc -c < "$CACHE_FILE")
        echo "✓ Airport cache exists (${CACHE_SIZE} bytes)"
    fi
}

# Run cache initialization
initialize_airport_cache

# Function to start the FastAPI application
start_fastapi() {
    echo "🐍 Starting FastAPI backend on $HOST:$PORT..."
    cd /app
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "🔄 Hot reload enabled for Python, templates, and static files..."
        exec uvicorn app:app --host $HOST --port $PORT --reload \
            --reload-dir /app/app \
            --reload-include "*.py" \
            --reload-include "*.html" \
            --reload-include "*.css" \
            --reload-include "*.js" \
            --log-level info
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