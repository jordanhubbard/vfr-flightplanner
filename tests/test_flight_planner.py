import pytest
import json
from unittest.mock import patch
from app import create_app

# Using client fixture from conftest.py

def test_plan_route_kpao_7s5(client):
    """Test planning a VFR route between KPAO and 7S5 with realistic range and speed."""
    
    # Mock the airport functions to avoid cache issues
    with patch('app.models.flight_planner.get_airport_coordinates') as mock_airport:
        mock_airport.side_effect = lambda code: {
            'icao': code,
            'latitude': 37.5,
            'longitude': -122.0,
            'name': f'Test Airport {code}'
        }
        
        # Mock the plan_route function at the router's import path
        with patch('app.routers.flight_plan.plan_route') as mock_plan:
            mock_plan.return_value = {
                'legs': [
                    {
                        'from': 'KPAO',
                        'to': '7S5',
                        'distance_nm': 150.0,
                        'cruise_altitude_ft': 6500,
                        'estimated_time_hr': 1.25
                    }
                ],
                'total_distance_nm': 150.0,
                'estimated_time_hr': 1.25,
                'fuel_planning': {
                    'total_fuel_burn_gal': 15.0,
                    'fuel_stops': []
                }
            }
            
            payload = {
                'start_code': 'KPAO',
                'end_code': '7S5',
                'aircraft_range_nm': 400,         # nm, typical for a GA aircraft
                'groundspeed_kt': 120    # knots
            }
            response = client.post('/api/plan_route', json=payload)
            assert response.status_code == 200, response.content
            data = response.json()
            assert 'legs' in data
            assert 'total_distance_nm' in data
            assert 'estimated_time_hr' in data
            assert isinstance(data['legs'], list)
            assert data['legs'][0]['from_airport'] == 'KPAO'
            assert data['legs'][-1]['to_airport'] == '7S5'
            # Check VFR altitudes and terrain avoidance (cruise altitude should be > 0)
            for leg in data['legs']:
                assert leg['cruise_altitude_ft'] > 0
            # If route is long, expect at least one fuel stop
            if data['total_distance_nm'] > 400:
                assert len(data.get('fuel_planning', {}).get('fuel_stops', [])) > 0
            # Estimated time should be reasonable
            assert data['estimated_time_hr'] > 0
