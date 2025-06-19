from flask import Blueprint, render_template, request, jsonify
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main index page."""
    # Get coordinates from URL parameters, defaulting to None if not provided
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    return render_template('index.html',
                         api_key=os.getenv('OPENWEATHERMAP_API_KEY', ''),
                         initial_lat=lat,
                         initial_lon=lon)

@main_bp.route('/get_area_forecast', methods=['POST'])
def get_area_forecast():
    """Get area weather forecast for specified airport code"""
    try:
        from app.models.airport import get_airport_coordinates
        from app.models.weather import get_weather_data
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        airport_code = data.get('airport_code', '').strip().upper()
        forecast_date = data.get('forecast_date')
        
        if not airport_code:
            return jsonify({
                'error': 'Missing airport code',
                'details': 'Airport code is required'
            }), 400
            
        # Get airport coordinates
        airport_data = get_airport_coordinates(airport_code)
        if not airport_data:
            return jsonify({
                'error': 'Airport not found',
                'details': f'No airport found with code {airport_code}'
            }), 404
            
        lat = airport_data['latitude']
        lon = airport_data['longitude']
        
        # Calculate days from today to requested date
        if forecast_date:
            try:
                requested_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()
                today = datetime.now().date()
                days_from_today = (requested_date - today).days
                if days_from_today < 0:
                    return jsonify({
                        'error': 'Invalid date',
                        'details': 'Cannot request weather data for past dates'
                    }), 400
                days = max(days_from_today + 1, 7)  # Get at least 7 days or enough to include requested date
            except ValueError:
                return jsonify({
                    'error': 'Invalid date format',
                    'details': 'Date must be in YYYY-MM-DD format'
                }), 400
        else:
            days = 7  # Default to 7 days
            
        # Get weather data for the airport location
        weather_data = get_weather_data(lat, lon, days, overlays=[])
        
        if not weather_data:
            return jsonify({
                'error': 'Failed to fetch weather data',
                'details': 'Weather service temporarily unavailable'
            }), 500
            
        # Add airport information to the response
        response_data = {
            'airport': {
                'code': airport_code,
                'name': airport_data.get('name', 'Unknown Airport'),
                'latitude': lat,
                'longitude': lon
            },
            'weather': weather_data,
            'forecast_date': forecast_date,
            'radius_nm': 50  # Area forecast is for 50nm radius
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_area_forecast: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500
