import requests
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_weather_data(lat, lon, days=7, overlays=None):
    """
    Get weather forecast data for a specific location.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        days (int): Number of forecast days (1-16)
        overlays (list): List of active weather overlays
        
    Returns:
        dict: Weather forecast data
    """
    try:
        # Ensure days is within valid range
        days = max(1, min(16, days))
        
        # Get Open-Meteo forecast data with error handling
        meteo_data = {}
        try:
            meteo_data = get_open_meteo_forecast(lat, lon, days)
        except Exception as e:
            logger.error(f"Failed to fetch Open-Meteo data: {str(e)}")
            meteo_data = get_fallback_weather_data(lat, lon, days)
        
        # Get OpenWeatherMap data if we have an API key
        api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        owm_data = {}
        
        if api_key:
            try:
                owm_data = get_openweathermap_data(lat, lon, api_key)
            except Exception as e:
                logger.error(f"Failed to fetch OpenWeatherMap data: {str(e)}")
                owm_data = {}
        
        # Combine data from both sources
        combined_data = {
            'location': {
                'latitude': lat,
                'longitude': lon
            },
            'current': {
                **meteo_data.get('current', {}),
                **owm_data.get('current', {})
            },
            'hourly': meteo_data.get('hourly', {}),
            'daily': meteo_data.get('daily', {}),
            'overlays': get_overlay_urls(lat, lon, overlays, api_key) if api_key else {}
        }
        
        return combined_data
        
    except Exception as e:
        logger.error(f"Error in get_weather_data: {str(e)}")
        return get_fallback_weather_data(lat, lon, days)


def get_open_meteo_forecast(lat, lon, days):
    """
    Get forecast data from Open-Meteo API.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        days (int): Number of forecast days
        
    Returns:
        dict: Forecast data
    """
    try:
        # Build the Open-Meteo API URL with all required parameters
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,relativehumidity_2m,dewpoint_2m,apparent_temperature,"
            f"precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,"
            f"weathercode,pressure_msl,surface_pressure,cloudcover,cloudcover_low,"
            f"cloudcover_mid,cloudcover_high,visibility,evapotranspiration,"
            f"et0_fao_evapotranspiration,vapor_pressure_deficit,windspeed_10m,"
            f"windspeed_80m,windspeed_120m,windspeed_180m,winddirection_10m,"
            f"winddirection_80m,winddirection_120m,winddirection_180m,windgusts_10m,"
            f"shortwave_radiation,direct_radiation,direct_normal_irradiance,"
            f"diffuse_radiation,is_day"
            f"&daily=weathercode,temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
            f"apparent_temperature_min,sunrise,sunset,uv_index_max,uv_index_clear_sky_max,"
            f"precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_hours,"
            f"precipitation_probability_max,windspeed_10m_max,windgusts_10m_max,"
            f"winddirection_10m_dominant,shortwave_radiation_sum,et0_fao_evapotranspiration"
            f"&current_weather=true&windspeed_unit=mph&precipitation_unit=inch"
            f"&timeformat=unixtime&timezone=auto&forecast_days={days}"
        )
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Process the data into a more usable format
        processed_data = process_open_meteo_data(data)
        
        return processed_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Open-Meteo data: {str(e)}")
        return {'forecast': [], 'current': {}}


def process_open_meteo_data(data):
    """
    Process raw Open-Meteo API data into a more usable format.
    
    Args:
        data (dict): Raw API response data
        
    Returns:
        dict: Processed forecast and current weather data
    """
    try:
        result = {
            'forecast': [],
            'current': {}
        }
        
        # Process current weather
        if 'current_weather' in data:
            current = data['current_weather']
            result['current'] = {
                'temperature': current.get('temperature'),
                'windspeed': current.get('windspeed'),
                'winddirection': current.get('winddirection'),
                'weathercode': current.get('weathercode'),
                'time': current.get('time')
            }
        
        # Process daily forecast
        if 'daily' in data:
            daily = data['daily']
            time_array = daily.get('time', [])
            
            for i in range(len(time_array)):
                day_data = {
                    'date': time_array[i],
                    'weathercode': daily.get('weathercode', [])[i] if 'weathercode' in daily and i < len(daily['weathercode']) else None,
                    'temp_max': daily.get('temperature_2m_max', [])[i] if 'temperature_2m_max' in daily and i < len(daily['temperature_2m_max']) else None,
                    'temp_min': daily.get('temperature_2m_min', [])[i] if 'temperature_2m_min' in daily and i < len(daily['temperature_2m_min']) else None,
                    'apparent_temp_max': daily.get('apparent_temperature_max', [])[i] if 'apparent_temperature_max' in daily and i < len(daily['apparent_temperature_max']) else None,
                    'apparent_temp_min': daily.get('apparent_temperature_min', [])[i] if 'apparent_temperature_min' in daily and i < len(daily['apparent_temperature_min']) else None,
                    'sunrise': daily.get('sunrise', [])[i] if 'sunrise' in daily and i < len(daily['sunrise']) else None,
                    'sunset': daily.get('sunset', [])[i] if 'sunset' in daily and i < len(daily['sunset']) else None,
                    'uv_index': daily.get('uv_index_max', [])[i] if 'uv_index_max' in daily and i < len(daily['uv_index_max']) else None,
                    'precipitation_sum': daily.get('precipitation_sum', [])[i] if 'precipitation_sum' in daily and i < len(daily['precipitation_sum']) else None,
                    'precipitation_probability': daily.get('precipitation_probability_max', [])[i] if 'precipitation_probability_max' in daily and i < len(daily['precipitation_probability_max']) else None,
                    'windspeed_max': daily.get('windspeed_10m_max', [])[i] if 'windspeed_10m_max' in daily and i < len(daily['windspeed_10m_max']) else None,
                    'windgusts_max': daily.get('windgusts_10m_max', [])[i] if 'windgusts_10m_max' in daily and i < len(daily['windgusts_10m_max']) else None,
                    'winddirection': daily.get('winddirection_10m_dominant', [])[i] if 'winddirection_10m_dominant' in daily and i < len(daily['winddirection_10m_dominant']) else None,
                }
                result['forecast'].append(day_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing Open-Meteo data: {str(e)}")
        return {'forecast': [], 'current': {}}

def get_openweathermap_data(lat, lon, api_key):
    """
    Get current weather data from OpenWeatherMap API.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        api_key (str): OpenWeatherMap API key
        
    Returns:
        dict: Current weather data
    """
    if not api_key:
        return {'current': {}}
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant data
        current = {
            'description': data.get('weather', [{}])[0].get('description', ''),
            'icon': data.get('weather', [{}])[0].get('icon', ''),
            'humidity': data.get('main', {}).get('humidity'),
            'pressure': data.get('main', {}).get('pressure'),
            'visibility': data.get('visibility'),
            'clouds': data.get('clouds', {}).get('all')
        }
        
        return {'current': current}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching OpenWeatherMap data: {str(e)}")
        return {'current': {}}

def get_overlay_urls(lat, lon, overlays, api_key):
    """
    Generate URLs for weather map overlays.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        overlays (list): List of active overlays
        api_key (str): OpenWeatherMap API key
        
    Returns:
        dict: URLs for each requested overlay
    """
    if not api_key:
        return {}
        
    # Base zoom level - can be adjusted based on user preference
    zoom = 10
    
    # Calculate tile coordinates
    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - (lat + 90.0) / 360.0) * n)
    
    overlay_urls = {}
    
    # Map overlay types to their OpenWeatherMap layer codes
    overlay_types = {
        'clouds': 'clouds_new',
        'precipitation': 'precipitation_new',
        'wind': 'wind_new',
        'temp': 'temp_new'
    }
    
    # Generate URLs for each requested overlay
    for overlay in overlays:
        if overlay in overlay_types:
            layer = overlay_types[overlay]
            overlay_urls[overlay] = f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x_tile}/{y_tile}.png?appid={api_key}"
    
    return overlay_urls

def get_fallback_weather_data(lat, lon, days=7):
    """
    Generate fallback weather data when APIs are unavailable.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        days (int): Number of forecast days
        
    Returns:
        dict: Fallback weather data
    """
    import random
    from datetime import datetime, timedelta
    
    # Generate realistic fallback data based on location
    base_temp = 20 if abs(lat) < 30 else 10 if abs(lat) < 60 else 0
    
    current_time = datetime.now()
    hourly_times = [(current_time + timedelta(hours=i)).isoformat() for i in range(24)]
    daily_times = [(current_time + timedelta(days=i)).isoformat() for i in range(days)]
    
    # Generate wind data for aviation use
    wind_speed = random.randint(5, 25)  # 5-25 knots
    wind_direction = random.randint(0, 359)  # 0-359 degrees
    
    return {
        'current': {
            'temperature_2m': base_temp + random.randint(-5, 5),
            'relative_humidity_2m': random.randint(40, 80),
            'surface_pressure': random.randint(1010, 1025),
            'cloud_cover': random.randint(0, 100),
            'wind_speed_10m': wind_speed * 0.514444,  # Convert knots to m/s
            'wind_direction_10m': wind_direction
        },
        'hourly': {
            'time': hourly_times,
            'temperature_2m': [base_temp + random.randint(-3, 3) for _ in range(24)],
            'wind_speed_10m': [wind_speed * 0.514444 + random.uniform(-2, 2) for _ in range(24)],
            'wind_direction_10m': [wind_direction + random.randint(-30, 30) for _ in range(24)]
        },
        'daily': {
            'time': daily_times,
            'temperature_2m_max': [base_temp + random.randint(0, 8) for _ in range(days)],
            'temperature_2m_min': [base_temp + random.randint(-8, 0) for _ in range(days)]
        }
    }
