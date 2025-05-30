#!/bin/bash
# Test runner script for Weather Forecasts application

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run tests with pytest
echo "Running tests..."
python -m pytest tests/ -v

# Return to the original directory
echo "Tests completed."
