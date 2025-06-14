from flask import Blueprint, request, jsonify, current_app
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
import logging
import xml.etree.ElementTree as ET

from app.utils.api_helpers import check_owm_api, check_meteo_api
from app.models.weather import get_weather_data
from app.models.airport import get_airports, get_airport_coordinates, get_metar_data
from app.models.flight_planner import plan_route

logger = logging.getLogger(__name__)

# Counter for OpenWeatherMap API calls
owm_api_calls = 0

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health')
def api_health():
    """Check health of all required APIs"""
    with ThreadPoolExecutor(max_workers=2) as executor:
        owm_future = executor.submit(check_owm_api)
        meteo_future = executor.submit(check_meteo_api)
        
        owm_result = owm_future.result()
        meteo_result = meteo_future.result()
        
        return jsonify({
            'openweathermap': owm_result,
            'openmeteo': meteo_result
        })

@api_bp.route('/weather', methods=['POST'])
def get_weather():
    """Get weather forecast for specified coordinates"""
    try:
        data = request.get_json()
        
        # Extract parameters from request
        lat = data.get('lat')
        lon = data.get('lon')
        days = data.get('days', 7)  # Default to 7 days if not specified
        overlays = data.get('overlays', [])  # Get active overlays
        
        # Log request parameters
        logger.info(f'Weather request for coordinates: {lat}, {lon} with {days} days forecast')
        
        if not all(isinstance(x, (int, float)) for x in [lat, lon]):
            return jsonify({
                'error': 'Invalid coordinates',
                'message': 'Latitude and longitude must be valid numbers'
            }), 400
            
        if not isinstance(days, int) or days < 1 or days > 16:
            return jsonify({
                'error': 'Invalid days parameter',
                'message': 'Days must be an integer between 1 and 16'
            }), 400
            
        # Get weather data from the weather model
        weather_data = get_weather_data(lat, lon, days, overlays)
        
        return jsonify(weather_data)
        
    except Exception as e:
        logger.error(f"Error in get_weather: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': str(e)
        }), 500

@api_bp.route('/airports', methods=['GET'])
def airports():
    """Get airports within a radius of a location"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=50, type=int)
        
        if not all([lat, lon]):
            return jsonify({
                'error': 'Missing parameters',
                'message': 'Latitude and longitude are required'
            }), 400
            
        # Get airports from the airport model
        airports_data = get_airports(lat, lon, radius)
        
        return jsonify(airports_data)
        
    except Exception as e:
        logger.error(f"Error in airports: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': str(e)
        }), 500

@api_bp.route('/airport', methods=['GET'])
def airport():
    """Get coordinates for an airport by ICAO or IATA code"""
    try:
        code = request.args.get('code', '').strip().upper()
        
        if not code:
            return jsonify({
                'error': 'Missing parameter',
                'message': 'Airport code is required'
            }), 400
            
        # Get airport coordinates from the airport model
        airport_data = get_airport_coordinates(code)
        
        if not airport_data:
            return jsonify({
                'error': 'Not found',
                'message': f'No airport found with code {code}'
            }), 404
            
        return jsonify(airport_data)
        
    except Exception as e:
        logger.error(f"Error in airport: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': str(e)
        }), 500

@api_bp.route('/metar', methods=['GET'])
def metar():
    """Get METAR data for airports"""
    try:
        codes = request.args.get('codes', '')
        
        if not codes:
            return jsonify({
                'error': 'Missing parameter',
                'message': 'Airport codes are required'
            }), 400
            
        # Split codes by comma and convert to uppercase
        icao_codes = [code.strip().upper() for code in codes.split(',')]
        
        # Get METAR data from the airport model
        metar_data = get_metar_data(icao_codes)
        
        return jsonify(metar_data)
        
    except Exception as e:
        logger.error(f"Error in metar: {str(e)}")
        return jsonify({
            'error': 'Server error',
            'message': str(e)
        }), 500

@api_bp.route('/plan_route', methods=['POST'])
def plan_route_api():
    """Plan a VFR route between two airports with terrain, VFR, and fuel stops."""
    try:
        data = request.get_json()
        from_code = data.get('from', '').strip().upper()
        to_code = data.get('to', '').strip().upper()
        aircraft_range = float(data.get('range', 400))
        groundspeed = float(data.get('groundspeed', 120))
        if not from_code or not to_code:
            return jsonify({'error': 'Missing required parameters'}), 400
        route = plan_route(from_code, to_code, aircraft_range, groundspeed)
        if 'error' in route:
            return jsonify(route), 400
        return jsonify(route)
    except Exception as e:
        logger.error(f"Error in plan_route: {str(e)}")
        return jsonify({'error': 'Server error', 'message': str(e)}), 500
