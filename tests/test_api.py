import pytest
import json
from unittest.mock import patch, MagicMock

def test_api_health_endpoint(client):
    """Test the API health endpoint returns correct structure."""
    
    # Mock the API health check functions
    with patch('app.utils.api_helpers.check_owm_api') as mock_owm, \
         patch('app.utils.api_helpers.check_meteo_api') as mock_meteo:
        
        # Configure mocks to return test data
        mock_owm.return_value = {
            'status': True,
            'error': None,
            'timestamp': '2025-05-29T12:00:00',
            'api_calls': 0
        }
        
        mock_meteo.return_value = {
            'status': True,
            'error': None,
            'timestamp': '2025-05-29T12:00:00'
        }
        
        # Call the API health endpoint
        response = client.get('/api/health')
        
        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify structure
        assert 'openweathermap' in data
        assert 'openmeteo' in data
        assert data['openweathermap']['status'] is True
        assert data['openmeteo']['status'] is True

def test_weather_endpoint(client):
    """Test the weather endpoint with mocked data."""
    
    # Mock the get_weather_data function
    with patch('app.api.routes.get_weather_data') as mock_weather:
        
        # Configure mock to return test data
        mock_data = {
            'location': {
                'latitude': 37.7749,
                'longitude': -122.4194
            },
            'forecast': [
                {
                    'date': 1716940800,
                    'temp_max': 68,
                    'temp_min': 52
                }
            ],
            'current': {
                'temperature': 62,
                'windspeed': 10
            },
            'overlays': {}
        }
        mock_weather.return_value = mock_data
        
        # Call the weather endpoint
        response = client.post('/api/weather', 
                              json={
                                  'lat': 37.7749,
                                  'lon': -122.4194,
                                  'days': 7
                              },
                              content_type='application/json')
        
        # Check response
        assert response.status_code == 200
        
        # Verify the mock was called with the correct parameters
        assert mock_weather.called
        args, kwargs = mock_weather.call_args
        assert args[0] == 37.7749  # lat
        assert args[1] == -122.4194  # lon
        assert args[2] == 7  # days

def test_weather_endpoint_invalid_params(client):
    """Test the weather endpoint with invalid parameters."""
    
    # Test with missing coordinates
    response = client.post('/api/weather', 
                          json={
                              'days': 7
                          },
                          content_type='application/json')
    
    assert response.status_code == 400
    
    # Test with invalid days parameter
    response = client.post('/api/weather', 
                          json={
                              'lat': 37.7749,
                              'lon': -122.4194,
                              'days': 20  # More than 16 days
                          },
                          content_type='application/json')
    
    assert response.status_code == 400

def test_airports_endpoint(client):
    """Test the airports endpoint with mocked data."""
    
    # Mock the get_airports function
    with patch('app.api.routes.get_airports') as mock_airports:
        
        # Configure mock to return test data
        mock_data = {
            'count': 2,
            'airports': [
                {
                    'icao': 'KSFO',
                    'name': 'San Francisco International Airport',
                    'latitude': 37.6213,
                    'longitude': -122.3790,
                    'distance': 10.2
                },
                {
                    'icao': 'KOAK',
                    'name': 'Oakland International Airport',
                    'latitude': 37.7214,
                    'longitude': -122.2208,
                    'distance': 15.7
                }
            ]
        }
        mock_airports.return_value = mock_data
        
        # Call the airports endpoint
        response = client.get('/api/airports?lat=37.7749&lon=-122.4194&radius=20')
        
        # Check response
        assert response.status_code == 200
        
        # Since we're mocking the function, we should get exactly what we mocked
        # This avoids issues with actual API calls failing
        assert mock_airports.called
        args, kwargs = mock_airports.call_args
        assert args[0] == 37.7749  # lat
        assert args[1] == -122.4194  # lon
        assert args[2] == 20  # radius

def test_airport_endpoint(client):
    """Test the airport endpoint with mocked data."""
    
    # Mock the get_airport_coordinates function
    with patch('app.api.routes.get_airport_coordinates') as mock_airport:
        
        # Configure mock to return test data
        mock_data = {
            'icao': 'KSFO',
            'name': 'San Francisco International Airport',
            'city': 'San Francisco',
            'state': 'CA',
            'latitude': 37.6213,
            'longitude': -122.3790,
            'elevation': 13
        }
        mock_airport.return_value = mock_data
        
        # Call the airport endpoint
        response = client.get('/api/airport?code=KSFO')
        
        # Check response
        assert response.status_code == 200
        
        # Verify the mock was called with the correct parameter
        assert mock_airport.called
        args, kwargs = mock_airport.call_args
        assert args[0] == 'KSFO'
        
        # Test with invalid code
        mock_airport.return_value = None
        response = client.get('/api/airport?code=INVALID')
        assert response.status_code == 404
