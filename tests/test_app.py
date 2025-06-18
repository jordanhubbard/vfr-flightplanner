import pytest
from app import create_app
from app.config import TestingConfig

# Using app and client fixtures from conftest.py

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
