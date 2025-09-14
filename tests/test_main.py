import pytest
from app import create_app

# Using client fixture from conftest.py

def test_index_page(client):
    """Test the root UI endpoint returns 200 and contains expected content."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Weather' in response.content  # Adjust string as needed for your UI

# You can add more UI endpoint tests as needed
