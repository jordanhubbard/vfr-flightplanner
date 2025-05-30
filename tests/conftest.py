import pytest
import os
import sys
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

# Import the app factory after setting up the path
from app import create_app
from app.config import TestingConfig

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestingConfig)
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
