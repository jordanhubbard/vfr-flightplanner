"""
Async Weather Model.

Asynchronous functions for weather data retrieval and processing.
"""

import httpx
import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


async def get_weather_data_async(
    lat: float, 
    lon: float, 
    days: int = 7, 
    overlays: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get weather forecast data for a specific location asynchronously.
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of forecast days (1-16)
        overlays: List of active weather overlays
        
    Returns:
        Weather forecast data
    """
    try:
        # Ensure days is within valid range
        days = max(1, min(16, days))
        
        # Create async HTTP client
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch data from multiple sources concurrently
            tasks = []
            
            # Always fetch Open-Meteo data
            tasks.append(get_open_meteo_forecast_async(client, lat, lon, days))
            
            # Fetch OpenWeatherMap data if we have an API key
            api_key = os.getenv('OPENWEATHERMAP_API_KEY')
            if api_key:
                tasks.append(get_openweathermap_data_async(client, lat, lon, api_key))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            meteo_data = results[0] if not isinstance(results[0], Exception) else {}
            owm_data = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else {}
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    source = "Open-Meteo" if i == 0 else "OpenWeatherMap"
                    logger.error(f"Failed to fetch {source} data: {result}")
            
            # Safely get overlay URLs
            overlays_data = {}
            if api_key:
                overlays_data = await get_overlay_urls_async(client, lat, lon, overlays, api_key)
            
            # Combine data from both sources
            combined_data = {
                'location': {
                    'latitude': lat,
                    'longitude': lon
                },
                'current': {
                    **(meteo_data.get('current', {}) if isinstance(meteo_data, dict) else {}),
                    **(owm_data.get('current', {}) if isinstance(owm_data, dict) else {})
                },
                'hourly': meteo_data.get('hourly', {}) if isinstance(meteo_data, dict) else {},
                'daily': meteo_data.get('daily', {}) if isinstance(meteo_data, dict) else {},
                'overlays': overlays_data
            }
            
            return combined_data
            
    except Exception as e:
        logger.error(f"Error in get_weather_data_async: {e}")
        return await get_fallback_weather_data_async(lat, lon, days)


async def get_open_meteo_forecast_async(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    days: int
) -> Dict[str, Any]:
    """
    Get forecast data from Open-Meteo API asynchronously.
    
    Args:
        client: HTTP client instance
        lat: Latitude
        lon: Longitude
        days: Number of forecast days
        
    Returns:
        Forecast data
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
        
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Process the data into a more usable format
        processed_data = process_open_meteo_data(data)
        
        return processed_data
        
    except httpx.HTTPError as e:
        logger.error(f"Error fetching Open-Meteo data: {e}")
        return {'forecast': [], 'current': {}}


async def get_openweathermap_data_async(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    api_key: str
) -> Dict[str, Any]:
    """
    Get current weather data from OpenWeatherMap API asynchronously.
    
    Args:
        client: HTTP client instance
        lat: Latitude
        lon: Longitude
        api_key: OpenWeatherMap API key
        
    Returns:
        Current weather data
    """
    if not api_key:
        return {'current': {}}
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant data
        current = {
            'description': data.get('weather', [{}])[0].get('description', ''),
            'icon': data.get('weather', [{}])[0].get('icon', ''),
            'humidity': data.get('main', {}).get('humidity'),
            'pressure': data.get('main', {}).get('pressure'),
            'visibility': data.get('visibility'),
            'clouds': data.get('clouds', {}).get('all'),
            'uv_index': None,  # Would need separate API call
            'wind_speed': data.get('wind', {}).get('speed'),
            'wind_direction': data.get('wind', {}).get('deg'),
            'wind_gust': data.get('wind', {}).get('gust'),
        }
        
        return {'current': current}
        
    except httpx.HTTPError as e:
        logger.error(f"Error fetching OpenWeatherMap data: {e}")
        return {'current': {}}


async def get_overlay_urls_async(
    client: httpx.AsyncClient,
    lat: float,
    lon: float,
    overlays: Optional[List[str]],
    api_key: str
) -> Dict[str, str]:
    """
    Get weather overlay URLs asynchronously.
    
    Args:
        client: HTTP client instance
        lat: Latitude
        lon: Longitude
        overlays: List of requested overlays
        api_key: OpenWeatherMap API key
        
    Returns:
        Dictionary of overlay URLs
    """
    if not overlays or not api_key:
        return {}
    
    overlay_urls = {}
    
    try:
        # OpenWeatherMap map layers
        zoom = 6
        x = int((lon + 180) / 360 * (2 ** zoom))
        y = int((1 - (lat + 90) / 180) * (2 ** zoom))
        
        layer_map = {
            'precipitation': 'precipitation_new',
            'clouds': 'clouds_new',
            'pressure': 'pressure_new',
            'wind': 'wind_new',
            'temperature': 'temp_new'
        }
        
        for overlay in overlays:
            if overlay in layer_map:
                layer = layer_map[overlay]
                url = f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x}/{y}.png?appid={api_key}"
                overlay_urls[overlay] = url
        
        return overlay_urls
        
    except Exception as e:
        logger.error(f"Error generating overlay URLs: {e}")
        return {}


async def get_fallback_weather_data_async(
    lat: float,
    lon: float,
    days: int = 7
) -> Dict[str, Any]:
    """
    Get fallback weather data when primary sources fail.
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of forecast days
        
    Returns:
        Basic weather data structure
    """
    try:
        # Generate basic forecast structure
        forecast_data = []
        base_time = datetime.now()
        
        for i in range(days):
            forecast_date = base_time + timedelta(days=i)
            day_data = {
                'date': int(forecast_date.timestamp()),
                'weathercode': 1,  # Clear sky
                'temp_max': 70,  # Default values
                'temp_min': 50,
                'apparent_temp_max': 70,
                'apparent_temp_min': 50,
                'sunrise': int((forecast_date.replace(hour=6, minute=0, second=0)).timestamp()),
                'sunset': int((forecast_date.replace(hour=18, minute=0, second=0)).timestamp()),
                'uv_index': 5,
                'precipitation_sum': 0,
                'precipitation_probability': 0,
                'windspeed_max': 10,
                'windgusts_max': 15,
                'winddirection': 270,
            }
            forecast_data.append(day_data)
        
        return {
            'location': {
                'latitude': lat,
                'longitude': lon
            },
            'current': {
                'temperature': 65,
                'windspeed': 10,
                'winddirection': 270,
                'weathercode': 1,
                'time': int(datetime.now().timestamp())
            },
            'forecast': forecast_data,
            'daily': {},
            'hourly': {},
            'overlays': {}
        }
        
    except Exception as e:
        logger.error(f"Error in get_fallback_weather_data_async: {e}")
        return {
            'location': {'latitude': lat, 'longitude': lon},
            'current': {},
            'forecast': [],
            'daily': {},
            'hourly': {},
            'overlays': {}
        }


def process_open_meteo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw Open-Meteo API data into a more usable format.
    
    Args:
        data: Raw API response data
        
    Returns:
        Processed forecast and current weather data
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
                    'weathercode': _safe_list_get(daily, 'weathercode', i),
                    'temp_max': _safe_list_get(daily, 'temperature_2m_max', i),
                    'temp_min': _safe_list_get(daily, 'temperature_2m_min', i),
                    'apparent_temp_max': _safe_list_get(daily, 'apparent_temperature_max', i),
                    'apparent_temp_min': _safe_list_get(daily, 'apparent_temperature_min', i),
                    'sunrise': _safe_list_get(daily, 'sunrise', i),
                    'sunset': _safe_list_get(daily, 'sunset', i),
                    'uv_index': _safe_list_get(daily, 'uv_index_max', i),
                    'precipitation_sum': _safe_list_get(daily, 'precipitation_sum', i),
                    'precipitation_probability': _safe_list_get(daily, 'precipitation_probability_max', i),
                    'windspeed_max': _safe_list_get(daily, 'windspeed_10m_max', i),
                    'windgusts_max': _safe_list_get(daily, 'windgusts_10m_max', i),
                    'winddirection': _safe_list_get(daily, 'winddirection_10m_dominant', i),
                }
                result['forecast'].append(day_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing Open-Meteo data: {e}")
        return {'forecast': [], 'current': {}}


def _safe_list_get(data: Dict[str, Any], key: str, index: int) -> Any:
    """Safely get a value from a list in the data dictionary."""
    try:
        if key in data and index < len(data[key]):
            return data[key][index]
        return None
    except (KeyError, IndexError, TypeError):
        return None 