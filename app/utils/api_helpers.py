import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Counter for OpenWeatherMap API calls
owm_api_calls = 0

def check_owm_api():
    """
    Check OpenWeatherMap API health.
    
    Returns:
        dict: API health status
    """
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
