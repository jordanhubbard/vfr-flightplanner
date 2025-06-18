import pytest
import json
from app import create_app

# Using client fixture from conftest.py

def test_plan_route_kpao_7s5(client):
    """Test planning a VFR route between KPAO and 7S5 with realistic range and speed."""
    payload = {
        'from': 'KPAO',
        'to': '7S5',
        'range': 400,         # nm, typical for a GA aircraft
        'groundspeed': 120    # knots
    }
    response = client.post('/api/plan_route', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200, response.data
    data = response.get_json()
    assert 'legs' in data
    assert 'total_distance_nm' in data
    assert 'estimated_time_hr' in data
    assert isinstance(data['legs'], list)
    assert data['legs'][0]['from'] == 'KPAO'
    assert data['legs'][-1]['to'] == '7S5'
    # Check VFR altitudes and terrain avoidance (cruise altitude should be > 0)
    for leg in data['legs']:
        assert leg['cruise_altitude_ft'] > 0
    # If route is long, expect at least one fuel stop
    if data['total_distance_nm'] > 400:
        assert len(data['fuel_stops']) > 0
    # Estimated time should be reasonable
    assert data['estimated_time_hr'] > 0
