import pytest
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

def test_index_page(client):
    """Test that the index page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Flight Planner' in response.data

def test_api_health(client):
    """Test the API health endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'openweathermap' in json_data
    assert 'openmeteo' in json_data
