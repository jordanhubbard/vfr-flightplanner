"""
Weather Router.

Provides endpoints for weather forecasting and meteorological data.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import WeatherRequest, WeatherResponse, AreaForecastRequest
from app.models.weather_async import get_weather_data_async
from app.models.airport import get_airport_coordinates

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/weather", response_model=WeatherResponse)
@limiter.limit("30/minute")
async def get_weather_forecast(
    request: Request,
    weather_request: WeatherRequest = Body(..., description="Weather forecast request")
) -> WeatherResponse:
    """
    Get weather forecast for specified coordinates.
    
    Args:
        request: FastAPI request object
        weather_request: Weather forecast request parameters
        
    Returns:
        WeatherResponse: Weather forecast data
        
    Raises:
        HTTPException: If weather data cannot be retrieved
    """
    try:
        logger.info(f"Weather request for coordinates: {weather_request.lat}, {weather_request.lon}")
        
        # Get weather data asynchronously
        weather_data = await get_weather_data_async(
            weather_request.lat,
            weather_request.lon,
            weather_request.days,
            weather_request.overlays
        )
        
        if not weather_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch weather data"
            )
        
        # Transform the weather data to match our response schema
        # This assumes the get_weather_data function returns data in the expected format
        # You may need to adjust this based on the actual return format
        
        return WeatherResponse(**weather_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_weather_forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail="Weather service temporarily unavailable"
        )


@router.post("/area_forecast")
@limiter.limit("10/minute")
async def get_area_forecast(
    request: Request,
    area_request: Dict[str, Any] = Body(..., description="Area forecast request")
) -> Dict[str, Any]:
    """
    Get area weather forecast for specified airport code.
    
    Args:
        request: FastAPI request object
        area_request: Area forecast request with airport_code and optional forecast_date
        
    Returns:
        Dict[str, Any]: Area weather forecast data
        
    Raises:
        HTTPException: If area forecast data cannot be retrieved
    """
    try:
        airport_code = area_request.get('airport_code', '').strip().upper()
        forecast_date = area_request.get('forecast_date')
        
        if not airport_code:
            raise HTTPException(
                status_code=400,
                detail="Airport code is required"
            )
            
        logger.info(f"Area forecast request for airport: {airport_code}")
        
        # Get airport coordinates
        airport_data = await asyncio.to_thread(get_airport_coordinates, airport_code)
        
        if not airport_data:
            raise HTTPException(
                status_code=404,
                detail=f"No airport found with code {airport_code}"
            )
            
        lat = airport_data['coordinates']['latitude']
        lon = airport_data['coordinates']['longitude']
        
        # Calculate days from today to requested date
        if forecast_date:
            try:
                requested_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()
                today = datetime.now().date()
                days_from_today = (requested_date - today).days
                if days_from_today < 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot request weather data for past dates"
                    )
                days = max(days_from_today + 1, 7)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Date must be in YYYY-MM-DD format"
                )
        else:
            days = 7
            
        # Get weather data for the airport location
        weather_data = await get_weather_data_async(lat, lon, days, overlays=[])
        
        if not weather_data:
            raise HTTPException(
                status_code=500,
                detail="Weather service temporarily unavailable"
            )
            
        # Build comprehensive response
        response_data = {
            'airport': {
                'code': airport_code,
                'name': airport_data.get('name', 'Unknown Airport'),
                'coordinates': {
                    'latitude': lat,
                    'longitude': lon
                }
            },
            'weather': weather_data,
            'forecast_date': forecast_date,
            'radius_nm': 50,
            'generated_at': datetime.now().isoformat()
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_area_forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail="Area forecast service temporarily unavailable"
        )


# Additional weather-related endpoints can be added here
# Examples:
# - Current conditions
# - Weather alerts
# - Historical weather data
# - Weather maps and overlays 