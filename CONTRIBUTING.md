# Contributing to Weather Forecasts

This document provides guidelines and instructions for contributing to the Weather Forecasts application.

## Project Structure

The application follows a modular structure:

```
weather-forecasts/
├── app/                    # Main application package
│   ├── __init__.py         # Application factory
│   ├── api/                # API endpoints
│   │   ├── __init__.py
│   │   └── routes.py       # API route definitions
│   ├── controllers/         # Controllers (route handlers, MVC)
│   │   ├── __init__.py
│   │   └── routes.py       # Main route definitions
│   ├── models/             # Data models
│   │   ├── __init__.py
│   │   ├── airport.py      # Airport-related functionality
│   │   └── weather.py      # Weather-related functionality
│   ├── static/             # Static assets
│   │   ├── css/
│   │   └── js/
│   ├── templates/          # HTML templates
│   │   └── index.html
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   ├── api_helpers.py  # API helper functions
│   │   ├── error_handlers.py # Error handling
│   │   └── request_handlers.py # Request handling
│   └── config.py           # Application configuration
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   ├── test_api.py         # API tests
│   └── test_app.py         # Application tests
├── .dockerignore           # Docker ignore file
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── docker-compose.yml      # Docker Compose configuration
├── docker-entrypoint.sh    # Docker entrypoint script
├── Dockerfile              # Docker build configuration
├── Makefile                # Build automation
├── pytest.ini              # Pytest configuration
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
└── setup.cfg               # Tool configuration
```

## Development Environment

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Docker (for containerized development)
- OpenWeatherMap API key

### Setting Up

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd weather-forecasts
   ```

2. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your OpenWeatherMap API key.

4. Set up the development environment:
   ```bash
   make setup
   ```

## Development Workflow

The project uses a Makefile to automate common tasks. Here are the main commands:

### Local Development

- **Setup environment**: `make setup`
- **Run application**: `make run`
- **Run tests**: `make test`
- **Run tests with coverage**: `make test-cov`
- **Lint code**: `make lint`
- **Auto-fix lint issues**: `make lint-fix`
- **Clean temporary files**: `make clean`
- **Deep clean (including venv)**: `make deep-clean`

### Docker Development

- **Build Docker image**: `make docker-build`
- **Run in Docker**: `make docker-run`
- **View Docker logs**: `make docker-logs`
- **Stop Docker container**: `make docker-stop`
- **Clean Docker resources**: `make docker-clean`

### Docker Compose

- **Start with Docker Compose**: `make compose-up`
- **View Docker Compose logs**: `make compose-logs`
- **Stop Docker Compose services**: `make compose-down`

## Testing

The project uses pytest for testing. Run tests with:

```bash
make test
```

For a coverage report:

```bash
make test-cov
```

## Code Style

The project follows PEP 8 style guidelines. Check code style with:

```bash
make lint
```

Fix code style issues automatically with:

```bash
make lint-fix
```

## Deployment

To deploy the application:

```bash
make deploy
```

This will run tests, build the Docker image, and prepare the application for deployment.

## Getting Help

For a list of all available make targets:

```bash
make help
```

## Important Note

You must run the app in Docker (see README). Local Python execution is not supported.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
