import pytest
import os
import sys
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

# Import the FastAPI app factory after setting up the path
from fastapi.testclient import TestClient
from app import create_app
from app.config import TestingSettings

@pytest.fixture
def app():
    """Create and configure a FastAPI app for testing."""
    settings = TestingSettings()
    app = create_app(settings)
    return app

@pytest.fixture
def client(app):
    """A test client for the FastAPI app."""
    return TestClient(app)
