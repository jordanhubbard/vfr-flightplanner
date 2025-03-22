.PHONY: run setup clean check-env dev

# Python virtual environment directory
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Check for required environment variables
check-env:
	@if [ ! -f .env ] && [ -z "$$OPENWEATHERMAP_API_KEY" ]; then \
		echo "\033[31mError: OpenWeatherMap API key not found!\033[0m"; \
		echo "Please either:"; \
		echo "1. Create a .env file with OPENWEATHERMAP_API_KEY=your_api_key"; \
		echo "2. Or set the OPENWEATHERMAP_API_KEY environment variable"; \
		echo "\nGet your API key at: https://openweathermap.org/api"; \
		exit 1; \
	fi

# Development target with hot reloading
dev: check-env $(VENV)
	@echo "Starting development server with hot reloading..."
	. $(VENV)/bin/activate && FLASK_ENV=development FLASK_DEBUG=1 FLASK_APP=app.py flask run

# Default target (production-like)
run: check-env $(VENV)
	. $(VENV)/bin/activate && FLASK_ENV=production FLASK_APP=app.py flask run

# Create and setup virtual environment
$(VENV):
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

setup: $(VENV)

# Clean up virtual environment and cache files
clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 
	rm -f *.log
