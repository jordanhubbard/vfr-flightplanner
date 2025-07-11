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
        data = response.json()
        
        # Verify structure
        assert 'services' in data
        assert 'openweathermap' in data['services']
        assert 'openmeteo' in data['services']
        assert data['services']['openweathermap']['status'] is True
        assert data['services']['openmeteo']['status'] is True
        assert 'overall_status' in data


def test_weather_endpoint(client):
    """Test the weather endpoint with mocked data."""
    
    # Mock the async get_weather_data function
    with patch('app.models.weather_async.get_weather_data_async') as mock_weather:
        
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
        
        # Call the weather endpoint with FastAPI TestClient
        response = client.post('/api/weather', 
                              json={
                                  'lat': 37.7749,
                                  'lon': -122.4194,
                                  'days': 7
                              })
        
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
                          })
    
    assert response.status_code == 422  # FastAPI returns 422 for validation errors
    
    # Test with invalid latitude (out of range)
    response = client.post('/api/weather', 
                          json={
                              'lat': 91.0,  # Invalid latitude
                              'lon': -122.4194,
                              'days': 7
                          })
    
    assert response.status_code == 422


def test_airports_endpoint(client):
    """Test the airports endpoint with mocked data."""
    
    # Mock the get_airports function
    with patch('app.models.airport.get_airports') as mock_airports:
        
        # Configure mock to return test data
        mock_data = {
            'airports': [
                {
                    'icao': 'KSFO',
                    'iata': 'SFO',
                    'name': 'San Francisco International Airport',
                    'coordinates': {
                        'latitude': 37.6213,
                        'longitude': -122.3790
                    },
                    'elevation': 13,
                    'country': 'US',
                    'region': 'CA'
                },
                {
                    'icao': 'KOAK',
                    'iata': 'OAK',
                    'name': 'Oakland International Airport',
                    'coordinates': {
                        'latitude': 37.7214,
                        'longitude': -122.2208
                    },
                    'elevation': 9,
                    'country': 'US',
                    'region': 'CA'
                }
            ]
        }
        mock_airports.return_value = mock_data
        
        # Call the airports endpoint
        response = client.post('/api/airports',
                              json={
                                  'lat': 37.7749,
                                  'lon': -122.4194,
                                  'radius': 20
                              })
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure matches FastAPI response schema
        assert 'airports' in data
        assert 'count' in data
        assert 'search_center' in data
        assert 'radius_nm' in data
        
        # Verify the mock was called with the correct parameters
        assert mock_airports.called
        args, kwargs = mock_airports.call_args
        assert args[0] == 37.7749  # lat
        assert args[1] == -122.4194  # lon
        assert args[2] == 20  # radius


def test_airport_endpoint(client):
    """Test the airport endpoint with mocked data."""
    
    # Mock the get_airport_coordinates function
    with patch('app.models.airport.get_airport_coordinates') as mock_airport:
        
        # Configure mock to return test data
        mock_data = {
            'icao': 'KSFO',
            'iata': 'SFO',
            'name': 'San Francisco International Airport',
            'coordinates': {
                'latitude': 37.6213,
                'longitude': -122.3790
            },
            'elevation': 13,
            'country': 'US',
            'region': 'CA'
        }
        mock_airport.return_value = mock_data
        
        # Call the airport endpoint
        response = client.get('/api/airport?code=KSFO')
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure matches FastAPI response schema
        assert 'airport' in data
        assert data['airport']['icao'] == 'KSFO'
        
        # Verify the mock was called with the correct parameter
        assert mock_airport.called
        args, kwargs = mock_airport.call_args
        assert args[0] == 'KSFO'
        
        # Test with invalid code
        mock_airport.return_value = None
        response = client.get('/api/airport?code=INVALID')
        assert response.status_code == 404


def test_plan_route_endpoint(client):
    """Test the flight plan endpoint with mocked data."""
    
    # Mock the plan_route function
    with patch('app.models.flight_planner.plan_route') as mock_plan:
        
        # Configure mock to return test data
        mock_data = {
            'legs': [
                {
                    'from': 'KJFK',
                    'to': 'KLAX',
                    'distance_nm': 2445.8,
                    'cruise_altitude_ft': 6500,
                    'estimated_time_hr': 17.47
                }
            ],
            'total_distance_nm': 2445.8,
            'estimated_time_hr': 17.47,
            'fuel_planning': {
                'total_fuel_burn_gal': 209.6,
                'fuel_stops': []
            }
        }
        mock_plan.return_value = mock_data
        
        # Call the flight plan endpoint
        response = client.post('/api/plan_route',
                              json={
                                  'start_code': 'KJFK',
                                  'end_code': 'KLAX',
                                  'aircraft_range_nm': 800,
                                  'groundspeed_kt': 140,
                                  'fuel_capacity_gal': 50.0,
                                  'fuel_burn_gph': 12.0,
                                  'avoid_terrain': False,
                                  'plan_fuel_stops': True,
                                  'cruising_altitude_ft': 6500
                              })
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure matches FastAPI response schema
        assert 'route_summary' in data
        assert 'legs' in data
        assert 'total_distance_nm' in data
        assert 'estimated_time_hr' in data
        
        # Verify the mock was called
        assert mock_plan.called
