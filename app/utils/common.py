"""
Common utilities and shared functions for the weather forecasts application.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional


def setup_logger(name: str) -> logging.Logger:
    """
    Create a standardized logger instance.
    
    Args:
        name: Logger name, typically __name__
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def handle_request_exception(e: Exception, context: str = "API request") -> Dict[str, Any]:
    """
    Standardized handling of requests exceptions.
    
    Args:
        e: The exception that occurred
        context: Context description for the error
        
    Returns:
        Standardized error response dictionary
    """
    if isinstance(e, requests.exceptions.Timeout):
        return {
            'status': False,
            'error': 'Request timed out',
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
    elif isinstance(e, requests.exceptions.ConnectionError):
        return {
            'status': False,
            'error': 'Connection failed',
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
    elif isinstance(e, requests.exceptions.RequestException):
        return {
            'status': False,
            'error': f'Request failed: {str(e)}',
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
    else:
        return {
            'status': False,
            'error': f'Unexpected error: {str(e)}',
            'context': context,
            'timestamp': datetime.now().isoformat()
        }


def make_safe_request(url: str, params: Optional[Dict] = None, timeout: int = 10) -> Optional[requests.Response]:
    """
    Make a safe HTTP request with standardized error handling.
    
    Args:
        url: URL to request
        params: Optional query parameters
        timeout: Request timeout in seconds
        
    Returns:
        Response object or None if request failed
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger = setup_logger(__name__)
        logger.error(f"Request to {url} failed: {str(e)}")
        return None


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude coordinates.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        True if coordinates are valid
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)
    except (ValueError, TypeError):
        return False


def format_error_response(error: str, details: str = None, status_code: int = 400) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
        details: Optional error details
        status_code: HTTP status code
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        'error': error,
        'timestamp': datetime.now().isoformat()
    }
    
    if details:
        response['details'] = details
        
    return response 