import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def check_owm_api():
    """
    Check OpenWeatherMap API health.
    
    Returns:
        dict: API health status
    """
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    if not api_key:
        return {
            'status': False,
            'error': 'OpenWeatherMap API key not set',
            'timestamp': datetime.now().isoformat(),
            'api_calls': 0
        }
        
    api_calls = 0
    try:
        # Increment API call counter
        api_calls += 1
        
        # Make a simple API call to check status (e.g., get current weather for a fixed location)
        url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        return {
            'status': True,
            'timestamp': datetime.now().isoformat(),
            'api_calls': api_calls
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'api_calls': api_calls
        }

def check_meteo_api():
    """
    Check Open-Meteo API health.
    
    Returns:
        dict: API health status
    """
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
