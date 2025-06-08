import pytest
from flask import url_for
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test the root UI endpoint returns 200 and contains expected content."""
    response = client.get(url_for('main.index'))
    assert response.status_code == 200
    assert b'Weather' in response.data  # Adjust string as needed for your UI

# You can add more UI endpoint tests as needed
