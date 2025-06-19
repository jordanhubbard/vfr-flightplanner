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
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            owm_future = executor.submit(check_owm_api)
            meteo_future = executor.submit(check_meteo_api)
            
            try:
                owm_result = owm_future.result(timeout=10)
            except Exception as e:
                logger.error(f"OWM API check failed: {str(e)}")
                owm_result = {
                    'status': False,
                    'error': 'Network connectivity issues',
                    'timestamp': datetime.now().isoformat(),
                    'api_calls': 0
                }
            
            try:
                meteo_result = meteo_future.result(timeout=10)
            except Exception as e:
                logger.error(f"Meteo API check failed: {str(e)}")
                meteo_result = {
                    'status': False,
                    'error': 'Network connectivity issues',
                    'timestamp': datetime.now().isoformat()
                }
            
            return jsonify({
                'openweathermap': owm_result,
                'openmeteo': meteo_result,
                'overall_status': 'degraded' if not (owm_result.get('status', False) or meteo_result.get('status', False)) else 'operational'
            })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'error': 'Health check failed',
            'message': str(e),
            'overall_status': 'error'
        }), 500

@api_bp.route('/weather', methods=['POST'])
def get_weather():
    """Get weather forecast for specified coordinates"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        lat = data.get('lat')
        lon = data.get('lon')
        days = data.get('days', 7)
        overlays = data.get('overlays', [])
        
        if lat is None or lon is None:
            return jsonify({'error': 'Missing required parameters: lat, lon'}), 400
            
        # Validate coordinates
        try:
            lat = float(lat)
            lon = float(lon)
            days = int(days)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid coordinate or days format'}), 400
            
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
            
        # Get weather data with fallback handling
        weather_data = get_weather_data(lat, lon, days, overlays)
        
        if not weather_data:
            return jsonify({'error': 'Failed to fetch weather data'}), 500
            
        return jsonify(weather_data)
        
    except Exception as e:
        logger.error(f"Error in get_weather: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Weather service temporarily unavailable'
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
    """Plan a VFR route between two airports with advanced fuel planning, terrain avoidance, and wind analysis."""
    try:
        data = request.get_json()
        from_code = data.get('from', '').strip().upper()
        to_code = data.get('to', '').strip().upper()
        aircraft_range = float(data.get('range', 400))
        groundspeed = float(data.get('groundspeed', 120))
        
        # New advanced parameters
        fuel_capacity = float(data.get('fuel_capacity', 50))
        fuel_burn_rate = float(data.get('fuel_burn_rate', 12))
        avoid_terrain = bool(data.get('avoid_terrain', False))
        plan_fuel_stops = bool(data.get('plan_fuel_stops', True))
        cruising_altitude = int(data.get('cruising_altitude', 6500))
        
        if not from_code or not to_code:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        route = plan_route(from_code, to_code, aircraft_range, groundspeed,
                          fuel_capacity, fuel_burn_rate, avoid_terrain, plan_fuel_stops,
                          cruising_altitude)
        if 'error' in route:
            return jsonify(route), 400
        return jsonify(route)
    except Exception as e:
        logger.error(f"Error in plan_route: {str(e)}")
        return jsonify({'error': 'Server error', 'message': str(e)}), 500

@api_bp.route('/airport-cache-status')
def airport_cache_status():
    """Check the status of airport cache files"""
    try:
        # Adjust paths to work with the new project structure
        cache_file = os.path.join(current_app.root_path, 'models', 'airports_cache.json')
        
        # Check if cache file exists and get its info
        cache_exists = os.path.exists(cache_file)
        
        status = {
            'airport_cache': {
                'exists': cache_exists,
                'size': os.path.getsize(cache_file) if cache_exists else 0,
                'modified': datetime.fromtimestamp(os.path.getmtime(cache_file)).isoformat() if cache_exists else None,
                'airport_count': 0
            },
            'overall_status': 'ready' if cache_exists else 'missing'
        }
        
        # Count airports in cache if file exists
        if cache_exists:
            try:
                import json
                with open(cache_file, 'r') as f:
                    airport_data = json.load(f)
                    status['airport_cache']['airport_count'] = len(airport_data) if isinstance(airport_data, list) else 0
            except Exception as e:
                logger.error(f"Error reading airport cache: {e}")
                
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error checking airport cache status: {e}")
        return jsonify({
            'error': 'Failed to check airport cache status',
            'details': str(e)
        }), 500

@api_bp.route('/refresh-airport-cache', methods=['POST'])
def refresh_airport_cache():
    """Manually trigger airport cache refresh"""
    try:
        import subprocess
        import threading
        
        def run_refresh():
            """Run airport cache refresh in background"""
            try:
                # Run the airport cache update scripts
                logger.info("Starting manual airport cache refresh...")
                
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(current_app.root_path))
                script_path = os.path.join(project_root, 'scripts', 'update_airport_cache.py')
                
                # Update airport cache with force flag
                result = subprocess.run(['python3', script_path, '--force'], 
                                       capture_output=True, text=True, timeout=120)
                logger.info(f"Airport cache update result: {result.returncode}, stdout: {result.stdout}, stderr: {result.stderr}")
                
                logger.info("Airport cache refresh completed")
                
            except Exception as e:
                logger.error(f"Error during airport cache refresh: {e}")
        
        # Start refresh in background thread
        refresh_thread = threading.Thread(target=run_refresh)
        refresh_thread.daemon = True
        refresh_thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'Airport cache refresh started in background'
        })
        
    except Exception as e:
        logger.error(f"Error starting airport cache refresh: {e}")
        return jsonify({
            'error': 'Failed to start airport cache refresh',
            'details': str(e)
        }), 500
