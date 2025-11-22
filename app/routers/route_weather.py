"""
Route Weather Router.

Provides endpoints for weather analysis along flight routes.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.weather_async import get_weather_data_async
from app.models.airport import get_airport_coordinates

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/route_weather_summary")
@limiter.limit("30/minute")
async def get_route_weather_summary(
    request: Request,
    route_request: Dict[str, Any] = Body(..., description="Route weather summary request")
) -> Dict[str, Any]:
    """
    Get overall weather summary for a flight route with waypoint details.
    
    Args:
        request: FastAPI request object
        route_request: Contains waypoints (list of lat/lon dicts) and optional parameters
        
    Returns:
        Dict containing overall route weather summary and conditions at each waypoint
        
    Raises:
        HTTPException: If weather data cannot be retrieved
    """
    try:
        waypoints = route_request.get('waypoints', [])
        interval_nm = route_request.get('interval_nm', 20)  # Sample every 20nm
        
        if not waypoints or len(waypoints) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 waypoints required for route weather"
            )
        
        logger.info(f"Route weather summary request for {len(waypoints)} waypoints")
        
        # Generate intermediate waypoints along the route
        all_waypoints = []
        for i in range(len(waypoints) - 1):
            start = waypoints[i]
            end = waypoints[i + 1]
            
            # Calculate distance between waypoints
            distance_nm = _calculate_distance(
                start['lat'], start['lon'],
                end['lat'], end['lon']
            )
            
            # Determine number of samples based on interval
            num_samples = max(2, int(distance_nm / interval_nm) + 1)
            
            # Add intermediate waypoints
            for j in range(num_samples if i == len(waypoints) - 2 else num_samples - 1):
                fraction = j / (num_samples - 1) if num_samples > 1 else 0
                lat = start['lat'] + (end['lat'] - start['lat']) * fraction
                lon = start['lon'] + (end['lon'] - start['lon']) * fraction
                
                all_waypoints.append({
                    'lat': lat,
                    'lon': lon,
                    'leg_index': i,
                    'fraction': fraction,
                    'distance_from_start': distance_nm * fraction
                })
        
        # Fetch weather for all waypoints concurrently
        weather_tasks = [
            get_weather_data_async(wp['lat'], wp['lon'], days=1, overlays=[])
            for wp in all_waypoints
        ]
        
        weather_results = await asyncio.gather(*weather_tasks, return_exceptions=True)
        
        # Process weather data and build summary
        route_weather = []
        wind_speeds = []
        cloud_covers = []
        visibilities = []
        precipitation_probabilities = []
        
        for i, weather_data in enumerate(weather_results):
            if isinstance(weather_data, Exception):
                logger.error(f"Failed to fetch weather for waypoint {i}: {weather_data}")
                continue
            
            if not weather_data or 'current' not in weather_data:
                continue
            
            current = weather_data.get('current', {})
            waypoint = all_waypoints[i]
            
            # Extract aviation-relevant data
            wind_speed_kt = round(current.get('windspeed', 0))
            wind_direction = round(current.get('winddirection', 0))
            temperature = round(current.get('temperature', 0))
            
            # Get hourly data for more detail
            hourly = weather_data.get('hourly', {})
            cloud_cover = 0
            visibility = 10  # Default good visibility
            precip_prob = 0
            
            if hourly and 'time' in hourly and len(hourly.get('time', [])) > 0:
                # Use first hour as representative
                if 'cloudcover' in hourly and len(hourly['cloudcover']) > 0:
                    cloud_cover = hourly['cloudcover'][0]
                if 'visibility' in hourly and len(hourly['visibility']) > 0:
                    # Convert meters to statute miles
                    visibility = round(hourly['visibility'][0] / 1609.34, 1)
                if 'precipitation_probability' in hourly and len(hourly['precipitation_probability']) > 0:
                    precip_prob = hourly['precipitation_probability'][0]
            
            waypoint_weather = {
                'lat': waypoint['lat'],
                'lon': waypoint['lon'],
                'leg_index': waypoint['leg_index'],
                'distance_from_start': round(waypoint['distance_from_start'], 1),
                'wind_speed_kt': wind_speed_kt,
                'wind_direction_deg': wind_direction,
                'temperature_c': temperature,
                'cloud_cover_percent': cloud_cover,
                'visibility_sm': visibility,
                'precipitation_probability': precip_prob,
                'weather_code': current.get('weathercode', 1)
            }
            
            route_weather.append(waypoint_weather)
            
            # Collect stats for summary
            wind_speeds.append(wind_speed_kt)
            cloud_covers.append(cloud_cover)
            visibilities.append(visibility)
            precipitation_probabilities.append(precip_prob)
        
        # Calculate overall summary statistics
        summary = {
            'total_waypoints': len(route_weather),
            'avg_wind_speed_kt': round(sum(wind_speeds) / len(wind_speeds), 1) if wind_speeds else 0,
            'max_wind_speed_kt': max(wind_speeds) if wind_speeds else 0,
            'avg_cloud_cover_percent': round(sum(cloud_covers) / len(cloud_covers), 1) if cloud_covers else 0,
            'min_visibility_sm': min(visibilities) if visibilities else 10,
            'max_precipitation_probability': max(precipitation_probabilities) if precipitation_probabilities else 0,
            'overall_conditions': _determine_flight_conditions(
                min(visibilities) if visibilities else 10,
                max(cloud_covers) if cloud_covers else 0
            ),
            'significant_weather': _identify_significant_weather(route_weather)
        }
        
        return {
            'summary': summary,
            'waypoint_weather': route_weather,
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_route_weather_summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Route weather service temporarily unavailable"
        )


@router.post("/point_weather_detail")
@limiter.limit("60/minute")
async def get_point_weather_detail(
    request: Request,
    point_request: Dict[str, Any] = Body(..., description="Point weather detail request")
) -> Dict[str, Any]:
    """
    Get detailed weather information for a specific point (lat/lon).
    Returns comprehensive aviation weather including winds aloft, clouds, visibility, etc.
    
    Args:
        request: FastAPI request object
        point_request: Contains lat, lon, and optional altitude
        
    Returns:
        Detailed weather data for the point
        
    Raises:
        HTTPException: If weather data cannot be retrieved
    """
    try:
        lat = point_request.get('lat')
        lon = point_request.get('lon')
        altitude_ft = point_request.get('altitude_ft', 6500)
        
        if lat is None or lon is None:
            raise HTTPException(
                status_code=400,
                detail="Latitude and longitude are required"
            )
        
        logger.info(f"Point weather detail request for {lat}, {lon} at {altitude_ft}ft")
        
        # Fetch comprehensive weather data
        weather_data = await get_weather_data_async(lat, lon, days=3, overlays=[])
        
        if not weather_data:
            raise HTTPException(
                status_code=500,
                detail="Weather service temporarily unavailable"
            )
        
        # Extract and format detailed aviation weather
        current = weather_data.get('current', {})
        hourly = weather_data.get('hourly', {})
        daily = weather_data.get('daily', {})
        
        # Format current conditions
        current_conditions = {
            'temperature_c': round(current.get('temperature', 0)),
            'temperature_f': round(current.get('temperature', 0) * 9/5 + 32),
            'wind_speed_kt': round(current.get('windspeed', 0)),
            'wind_direction_deg': round(current.get('winddirection', 0)),
            'weather_code': current.get('weathercode', 1),
            'weather_description': _get_weather_description(current.get('weathercode', 1))
        }
        
        # Extract hourly forecast (next 12 hours)
        hourly_forecast = []
        if hourly and 'time' in hourly:
            num_hours = min(12, len(hourly.get('time', [])))
            for i in range(num_hours):
                hour_data = {
                    'time': hourly['time'][i] if i < len(hourly.get('time', [])) else None,
                    'temperature_c': round(hourly['temperature_2m'][i]) if 'temperature_2m' in hourly and i < len(hourly['temperature_2m']) else None,
                    'wind_speed_kt': round(hourly['windspeed_10m'][i] * 1.94384) if 'windspeed_10m' in hourly and i < len(hourly['windspeed_10m']) else None,
                    'wind_direction_deg': round(hourly['winddirection_10m'][i]) if 'winddirection_10m' in hourly and i < len(hourly['winddirection_10m']) else None,
                    'cloud_cover_percent': round(hourly['cloudcover'][i]) if 'cloudcover' in hourly and i < len(hourly['cloudcover']) else None,
                    'precipitation_probability': round(hourly['precipitation_probability'][i]) if 'precipitation_probability' in hourly and i < len(hourly['precipitation_probability']) else None,
                    'visibility_sm': round(hourly['visibility'][i] / 1609.34, 1) if 'visibility' in hourly and i < len(hourly['visibility']) else 10
                }
                hourly_forecast.append(hour_data)
        
        # Get winds aloft if available (using different altitude wind data)
        winds_aloft = []
        if hourly:
            for alt_field, alt_ft in [
                ('windspeed_10m', 30),
                ('windspeed_80m', 250),
                ('windspeed_120m', 400),
                ('windspeed_180m', 600)
            ]:
                if alt_field in hourly and len(hourly[alt_field]) > 0:
                    wind_dir_field = alt_field.replace('windspeed', 'winddirection')
                    winds_aloft.append({
                        'altitude_ft': alt_ft,
                        'wind_speed_kt': round(hourly[alt_field][0] * 1.94384),
                        'wind_direction_deg': round(hourly[wind_dir_field][0]) if wind_dir_field in hourly and len(hourly[wind_dir_field]) > 0 else 0
                    })
        
        # Extract cloud layers from hourly data
        cloud_layers = []
        if hourly:
            if 'cloudcover_low' in hourly and len(hourly['cloudcover_low']) > 0:
                cloud_layers.append({
                    'level': 'Low',
                    'base_ft': 1000,
                    'coverage_percent': round(hourly['cloudcover_low'][0])
                })
            if 'cloudcover_mid' in hourly and len(hourly['cloudcover_mid']) > 0:
                cloud_layers.append({
                    'level': 'Mid',
                    'base_ft': 6500,
                    'coverage_percent': round(hourly['cloudcover_mid'][0])
                })
            if 'cloudcover_high' in hourly and len(hourly['cloudcover_high']) > 0:
                cloud_layers.append({
                    'level': 'High',
                    'base_ft': 20000,
                    'coverage_percent': round(hourly['cloudcover_high'][0])
                })
        
        return {
            'location': {
                'latitude': lat,
                'longitude': lon,
                'altitude_ft': altitude_ft
            },
            'current_conditions': current_conditions,
            'hourly_forecast': hourly_forecast,
            'winds_aloft': winds_aloft,
            'cloud_layers': cloud_layers,
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_point_weather_detail: {e}")
        raise HTTPException(
            status_code=500,
            detail="Point weather service temporarily unavailable"
        )


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in nautical miles using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3440.065  # Earth radius in nautical miles
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


def _determine_flight_conditions(visibility_sm: float, cloud_cover_percent: float) -> str:
    """Determine flight conditions based on visibility and cloud cover."""
    if visibility_sm >= 5 and cloud_cover_percent < 50:
        return "VFR"
    elif visibility_sm >= 3 and cloud_cover_percent < 75:
        return "MVFR"
    elif visibility_sm >= 1:
        return "IFR"
    else:
        return "LIFR"


def _identify_significant_weather(route_weather: List[Dict[str, Any]]) -> List[str]:
    """Identify significant weather conditions along the route."""
    significant = []
    
    # Check for high winds
    high_winds = [w for w in route_weather if w.get('wind_speed_kt', 0) > 25]
    if high_winds:
        significant.append(f"High winds ({max(w['wind_speed_kt'] for w in high_winds)}kt max)")
    
    # Check for low visibility
    low_vis = [w for w in route_weather if w.get('visibility_sm', 10) < 3]
    if low_vis:
        significant.append(f"Low visibility ({min(w['visibility_sm'] for w in low_vis)}sm min)")
    
    # Check for precipitation
    high_precip = [w for w in route_weather if w.get('precipitation_probability', 0) > 50]
    if high_precip:
        significant.append(f"Precipitation likely ({max(w['precipitation_probability'] for w in high_precip)}% max)")
    
    # Check for extensive cloud cover
    high_clouds = [w for w in route_weather if w.get('cloud_cover_percent', 0) > 80]
    if len(high_clouds) > len(route_weather) / 2:
        significant.append("Extensive cloud cover")
    
    if not significant:
        significant.append("No significant weather")
    
    return significant


def _get_weather_description(code: int) -> str:
    """Convert WMO weather code to description."""
    weather_codes = {
        0: 'Clear sky',
        1: 'Mainly clear',
        2: 'Partly cloudy',
        3: 'Overcast',
        45: 'Foggy',
        48: 'Depositing rime fog',
        51: 'Light drizzle',
        53: 'Moderate drizzle',
        55: 'Dense drizzle',
        61: 'Slight rain',
        63: 'Moderate rain',
        65: 'Heavy rain',
        71: 'Slight snow',
        73: 'Moderate snow',
        75: 'Heavy snow',
        77: 'Snow grains',
        80: 'Slight rain showers',
        81: 'Moderate rain showers',
        82: 'Violent rain showers',
        85: 'Slight snow showers',
        86: 'Heavy snow showers',
        95: 'Thunderstorm',
        96: 'Thunderstorm with slight hail',
        99: 'Thunderstorm with heavy hail'
    }
    return weather_codes.get(code, 'Unknown')
