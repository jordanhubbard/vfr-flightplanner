from flask import Flask, render_template, jsonify, request, send_from_directory
import requests
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('weather_data.log'),
        logging.StreamHandler()  # Keep console output as well
    ]
)
logger = logging.getLogger(__name__)

# Load .env from the same directory as app.py
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# Counter for OpenWeatherMap API calls
owm_api_calls = 0

@app.after_request
def add_header(response):
    """Add headers for caching control."""
    if app.debug:
        # In debug mode, prevent caching
        response.headers['Cache-Control'] = 'no-store'
    else:
        # In production, cache static files
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=600'
    return response

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors gracefully"""
    if request.path == '/ws':
        logger.warning("WebSocket connection attempted but not supported")
        return jsonify({
            "error": "WebSocket connections are not supported",
            "message": "This endpoint only supports HTTP requests"
        }), 404
    return jsonify({
        "error": "Not Found",
        "message": f"The requested URL {request.path} was not found on the server"
    }), 404

def check_owm_api():
    """Check OpenWeatherMap API health"""
    global owm_api_calls
    api_key = os.getenv('OPENWEATHERMAP_API_KEY', '')
    try:
        if not api_key:
            return {
                'status': False,
                'error': 'API key not configured',
                'timestamp': datetime.now().isoformat(),
                'api_calls': owm_api_calls
            }
            
        response = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?lat=0&lon=0&appid={api_key}',
            timeout=5
        )
        
        owm_api_calls += 1
        
        if response.status_code == 200:
            return {
                'status': True,
                'error': None,
                'timestamp': datetime.now().isoformat(),
                'api_calls': owm_api_calls
            }
        elif response.status_code == 401:
            return {
                'status': False,
                'error': 'Invalid API key',
                'timestamp': datetime.now().isoformat(),
                'api_calls': owm_api_calls
            }
        else:
            return {
                'status': False,
                'error': f'API returned status code {response.status_code}',
                'timestamp': datetime.now().isoformat(),
                'api_calls': owm_api_calls
            }
    except requests.exceptions.Timeout:
        return {
            'status': False,
            'error': 'Request timed out after 5 seconds',
            'timestamp': datetime.now().isoformat(),
            'api_calls': owm_api_calls
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': False,
            'error': 'Failed to connect to the API',
            'timestamp': datetime.now().isoformat(),
            'api_calls': owm_api_calls
        }
    except Exception as e:
        return {
            'status': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'api_calls': owm_api_calls
        }

def check_meteo_api():
    """Check Open-Meteo API health"""
    try:
        response = requests.get(
            'https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0',
            timeout=5
        )
        
        if response.status_code == 200:
            return {
                'status': True,
                'error': None,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': False,
                'error': f'API returned status code {response.status_code}',
                'timestamp': datetime.now().isoformat()
            }
    except requests.exceptions.Timeout:
        return {
            'status': False,
            'error': 'Request timed out after 5 seconds',
            'timestamp': datetime.now().isoformat()
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': False,
            'error': 'Failed to connect to the API',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@app.route('/api/health')
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

@app.route('/')
def index():
    # Get coordinates from URL parameters, defaulting to None if not provided
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    return render_template('index.html',
                         api_key=os.getenv('OPENWEATHERMAP_API_KEY', ''),
                         initial_lat=lat,
                         initial_lon=lon)

@app.route('/get_weather', methods=['POST'])
def get_weather():
    try:
        data = request.get_json()
        
        # Extract parameters from request
        lat = data.get('lat')
        lon = data.get('lon')
        days = data.get('days', 7)  # Default to 7 days if not specified
        overlays = data.get('overlays', [])  # Get active overlays
        
        # Log request parameters
        app.logger.info(f'Weather request for coordinates: {lat}, {lon} with {days} days forecast')
        
        if not all(isinstance(x, (int, float)) for x in [lat, lon]):
            return jsonify({
                'error': 'Invalid coordinates',
                'details': 'Latitude and longitude must be numbers'
            }), 400
            
        # Use the current system date
        today = datetime.now().date()
        app.logger.info(f'Using current date: {today}')
        
        max_forecast_days = 16  # Open-Meteo API limitation
        
        # Always use today as the start date
        requested_date = today
        
        # Adjust days if it would exceed the maximum forecast period
        if days > max_forecast_days:
            days = max_forecast_days
            app.logger.info(f'Adjusted forecast period to {days} days to stay within API limits')
        
        end_date = requested_date + timedelta(days=days-1)
            
        # Construct the API URL with parameters
        params = {
            'latitude': lat,
            'longitude': lon,
            'timezone': 'auto',
            'forecast_days': days,
            'hourly': [
                'temperature_2m',
                'windspeed_10m',
                'winddirection_10m',
                'windgusts_10m'
            ],
            'daily': [
                'weathercode',
                'temperature_2m_max',
                'temperature_2m_min',
                'precipitation_sum',
                'precipitation_probability_max',
                'cloudcover_mean',
                'visibility_mean'
            ],
            'models': 'best_match',  # Use best model for surface conditions
            'windspeed_unit': 'kn',  # Request wind speeds directly in knots
            'timeformat': 'unixtime',
            'past_days': 0,
            'current_weather': True  # Include current conditions
        }
        
        # Add overlay-specific parameters
        if 'wind' in overlays:
            params['hourly'].extend([
                'winddirection_10m',
                'windgusts_10m'
            ])
        
        if 'precipitation' in overlays:
            params['daily'].extend([
                'precipitation_hours',
                'precipitation_probability_mean'
            ])
        
        if 'temp' in overlays:
            params['daily'].extend([
                'apparent_temperature_max',
                'apparent_temperature_min'
            ])
            
        # Convert parameters to comma-separated strings
        params['hourly'] = ','.join(set(params['hourly']))  # Use set to remove duplicates
        params['daily'] = ','.join(set(params['daily']))
        
        url = 'https://api.open-meteo.com/v1/forecast'
        
        app.logger.info(f'Requesting weather data with params: {params}')
        
        # Get weather data from Open-Meteo
        meteo_response = requests.get(url, params=params)
        meteo_response.raise_for_status()
        meteo_data = meteo_response.json()
        
        # Log raw Open-Meteo response
        app.logger.info(f'Open-Meteo raw response: {meteo_data}')
        
        # Process hourly wind data to get daily values
        daily_wind_speed = []
        daily_wind_direction = []
        daily_wind_gusts = []
        daily_dates = []
        
        if 'hourly' in meteo_data:
            hourly_data = meteo_data['hourly']
            current_day = None
            day_wind_speeds = []
            day_wind_directions = []
            day_wind_gusts = []
            
            for i, time in enumerate(hourly_data['time']):
                # Convert unix timestamp to date
                date = datetime.fromtimestamp(time).strftime('%Y-%m-%d')
                
                if current_day is None:
                    current_day = date
                
                if date != current_day:
                    # Process previous day's data - use median for more stable values
                    day_wind_speeds.sort()
                    day_wind_gusts.sort()
                    mid_idx = len(day_wind_speeds) // 2
                    
                    daily_wind_speed.append(day_wind_speeds[mid_idx])
                    daily_wind_gusts.append(day_wind_gusts[mid_idx])
                    # Use the wind direction associated with the median wind speed
                    daily_wind_direction.append(day_wind_directions[day_wind_speeds.index(day_wind_speeds[mid_idx])])
                    daily_dates.append(current_day)
                    
                    # Reset for new day
                    current_day = date
                    day_wind_speeds = []
                    day_wind_directions = []
                    day_wind_gusts = []
                
                # Wind speeds are already in knots due to windspeed_unit parameter
                wind_speed = hourly_data['windspeed_10m'][i]
                wind_gust = hourly_data['windgusts_10m'][i]
                
                day_wind_speeds.append(wind_speed)
                day_wind_directions.append(hourly_data['winddirection_10m'][i])
                day_wind_gusts.append(wind_gust)
            
            # Process last day's data
            if day_wind_speeds:
                day_wind_speeds.sort()
                day_wind_gusts.sort()
                mid_idx = len(day_wind_speeds) // 2
                
                daily_wind_speed.append(day_wind_speeds[mid_idx])
                daily_wind_gusts.append(day_wind_gusts[mid_idx])
                daily_wind_direction.append(day_wind_directions[day_wind_speeds.index(day_wind_speeds[mid_idx])])
                daily_dates.append(current_day)
        
        # Get aviation data from OpenWeatherMap
        owm_url = 'https://api.openweathermap.org/data/3.0/onecall'
        owm_params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'minutely,alerts',
            'units': 'imperial',
            'appid': os.getenv('OPENWEATHERMAP_API_KEY', '')
        }
        
        owm_response = requests.get(owm_url, params=owm_params)
        owm_response.raise_for_status()
        owm_data = owm_response.json()
        
        # Log raw OpenWeatherMap response
        app.logger.info(f'OpenWeatherMap raw response: {owm_data}')
        
        # Combine the data
        combined_data = {
            'daily': {
                'time': daily_dates,
                'weathercode': meteo_data['daily']['weathercode'],
                'temperature_2m_max': meteo_data['daily']['temperature_2m_max'],
                'temperature_2m_min': meteo_data['daily']['temperature_2m_min'],
                'precipitation_sum': meteo_data['daily']['precipitation_sum'],
                'precipitation_probability_max': meteo_data['daily']['precipitation_probability_max'],
                'windspeed_10m_max': daily_wind_speed,
                'winddirection_10m_dominant': daily_wind_direction,
                'windgusts_10m_max': daily_wind_gusts,
                'cloudcover_mean': meteo_data['daily']['cloudcover_mean'],
                'visibility_mean': meteo_data['daily']['visibility_mean'],
                'pressure': [day.get('pressure', 1013.25) * 0.02953 for day in owm_data.get('daily', [])],  # Convert hPa to inHg
                'humidity': [day.get('humidity', 0) for day in owm_data.get('daily', [])]
            }
        }
        
        # Log processed data
        app.logger.info(f'Processed weather data: {combined_data}')
        
        # Create a detailed log entry for wind data validation
        for i, time in enumerate(combined_data['daily']['time']):
            wind_data = {
                'date': time,
                'wind_speed': combined_data['daily']['windspeed_10m_max'][i],
                'wind_direction': combined_data['daily']['winddirection_10m_dominant'][i],
                'wind_gusts': combined_data['daily']['windgusts_10m_max'][i]
            }
            app.logger.info(f'Wind data for {time}: {wind_data}')
        
        return jsonify(combined_data)
    except requests.exceptions.RequestException as e:
        app.logger.error(f'Error fetching weather data: {str(e)}')
        return jsonify({
            'error': 'Failed to fetch weather data',
            'details': str(e)
        }), 400
    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/get_airports', methods=['POST'])
def get_airports():
    try:
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')
        radius = data.get('radius', 50)  # Default radius in kilometers
        
        if not all(isinstance(x, (int, float)) for x in [lat, lon]):
            return jsonify({
                'error': 'Invalid coordinates',
                'details': 'Latitude and longitude must be numbers'
            }), 400
            
        # Overpass API query to find airports
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:25];
        (
          node["aeroway"="aerodrome"](around:{radius},{lat},{lon});
          way["aeroway"="aerodrome"](around:{radius},{lat},{lon});
          relation["aeroway"="aerodrome"](around:{radius},{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """
        
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        
        airports = []
        for element in response.json().get('elements', []):
            if 'tags' in element:
                airport = {
                    'name': element['tags'].get('name', 'Unnamed Airport'),
                    'type': element['tags'].get('aeroway', 'Unknown'),
                    'lat': element.get('lat', 0),
                    'lon': element.get('lon', 0),
                    'iata': element['tags'].get('iata', ''),
                    'icao': element['tags'].get('icao', '')
                }
                airports.append(airport)
        
        return jsonify({'airports': airports})
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f'Error fetching airports: {str(e)}')
        return jsonify({
            'error': 'Failed to fetch airports',
            'details': str(e)
        }), 400
    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/get_airport_coordinates', methods=['POST'])
def get_airport_coordinates():
    try:
        data = request.get_json()
        airport_code = data.get('airport_code', '').strip().upper()
        
        if not airport_code:
            return jsonify({
                'error': 'Invalid airport code',
                'details': 'Airport code is required'
            }), 400
            
        # Overpass API query to find airport
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # First try exact ICAO code match
        query = f"""
        [out:json][timeout:25];
        (
          node["icao"="{airport_code}"];
          way["icao"="{airport_code}"];
          relation["icao"="{airport_code}"];
        );
        out body;
        >;
        out skel qt;
        """
        
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        
        elements = response.json().get('elements', [])
        
        if not elements:
            # Try IATA code if ICAO not found
            query = f"""
            [out:json][timeout:25];
            (
              node["iata"="{airport_code}"];
              way["iata"="{airport_code}"];
              relation["iata"="{airport_code}"];
            );
            out body;
            >;
            out skel qt;
            """
            
            response = requests.post(overpass_url, data=query)
            response.raise_for_status()
            
            elements = response.json().get('elements', [])
            
            if not elements:
                # Try partial ICAO code match (for cases like KPAO)
                query = f"""
                [out:json][timeout:25];
                (
                  node["icao"~"{airport_code}"];
                  way["icao"~"{airport_code}"];
                  relation["icao"~"{airport_code}"];
                );
                out body;
                >;
                out skel qt;
                """
                
                response = requests.post(overpass_url, data=query)
                response.raise_for_status()
                
                elements = response.json().get('elements', [])
                
                if not elements:
                    # Try searching by name as a last resort
                    query = f"""
                    [out:json][timeout:25];
                    (
                      node["name"~"{airport_code}", "aeroway"];
                      way["name"~"{airport_code}", "aeroway"];
                      relation["name"~"{airport_code}", "aeroway"];
                    );
                    out body;
                    >;
                    out skel qt;
                    """
                    
                    response = requests.post(overpass_url, data=query)
                    response.raise_for_status()
                    
                    elements = response.json().get('elements', [])
                    
                    if not elements:
                        return jsonify({
                            'error': 'Airport not found',
                            'details': f'No airport found with code {airport_code}. Try using the full ICAO code (e.g., KPAO) or IATA code.'
                        }), 404
        
        # Get the first matching airport
        airport = elements[0]
        
        # Get coordinates
        if 'lat' in airport and 'lon' in airport:
            return jsonify({
                'lat': airport['lat'],
                'lon': airport['lon'],
                'name': airport.get('tags', {}).get('name', 'Unknown Airport'),
                'icao': airport.get('tags', {}).get('icao', ''),
                'iata': airport.get('tags', {}).get('iata', '')
            })
        else:
            # Try to get coordinates from the first node of a way or relation
            if 'nodes' in airport:
                # Get the first node's coordinates
                node_id = airport['nodes'][0]
                node_query = f"""
                [out:json][timeout:25];
                node({node_id});
                out body;
                """
                node_response = requests.post(overpass_url, data=node_query)
                node_response.raise_for_status()
                node_data = node_response.json()
                
                if node_data.get('elements') and 'lat' in node_data['elements'][0] and 'lon' in node_data['elements'][0]:
                    node = node_data['elements'][0]
                    return jsonify({
                        'lat': node['lat'],
                        'lon': node['lon'],
                        'name': airport.get('tags', {}).get('name', 'Unknown Airport'),
                        'icao': airport.get('tags', {}).get('icao', ''),
                        'iata': airport.get('tags', {}).get('iata', '')
                    })
            
            return jsonify({
                'error': 'Invalid airport data',
                'details': 'Airport coordinates not found'
            }), 404
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to fetch airport data',
            'details': str(e)
        }), 400
    except Exception as e:
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True) 