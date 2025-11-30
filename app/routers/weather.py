"""
Weather Router.

Provides endpoints for weather forecasting and meteorological data.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Body, Request, Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import WeatherRequest, WeatherResponse, AreaForecastRequest, WeatherData, AirportWeather
from app.schemas.common import Coordinates
from app.models.weather_async import get_weather_data_async
from app.models.airport import get_airport_coordinates, get_metar_data

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
        response = _build_weather_response(weather_data, weather_request)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_weather_forecast: {e}")
        raise HTTPException(
            status_code=500,
            detail="Weather service temporarily unavailable"
        )


@router.get("/weather/{airport_code}", response_model=AirportWeather)
@limiter.limit("60/minute")
async def get_airport_weather(
    request: Request,
    airport_code: str = Path(..., description="Airport ICAO or IATA code", min_length=3, max_length=4),
) -> AirportWeather:
    """
    Get simplified current weather for a specific airport.

    This endpoint is designed for the frontend weather UI and returns a concise
    summary built primarily from METAR data.
    """
    code = airport_code.strip().upper()
    try:
        logger.info(f"Airport weather request for code: {code}")

        # Look up airport in local cache (includes METAR if available)
        airport_data = await asyncio.to_thread(get_airport_coordinates, code)
        if not airport_data:
            raise HTTPException(
                status_code=404,
                detail=f"No airport found with code {code}",
            )

        metar = airport_data.get("metar")

        # If METAR wasn't already attached, fetch it explicitly
        if not metar:
            icao = airport_data.get("icao") or code
            if icao:
                metar_map = await asyncio.to_thread(get_metar_data, [icao])
                metar = metar_map.get(icao)

        if not metar:
            raise HTTPException(
                status_code=503,
                detail="METAR data unavailable for this airport",
            )

        # Derive ceiling from cloud layers (lowest BKN/OVC layer)
        ceiling_ft = 0.0
        cloud_layers = metar.get("cloud_layers") or []
        for layer in cloud_layers:
            cover = layer.get("cover")
            base = layer.get("base")
            if cover in ("BKN", "OVC") and base is not None:
                base_val = float(base)
                if ceiling_ft == 0.0 or base_val < ceiling_ft:
                    ceiling_ft = base_val

        # Build human-readable conditions string
        flight_category = metar.get("flight_category") or "Unknown"
        conditions = f"{flight_category} conditions"

        temperature_f = metar.get("temperature_f")
        if temperature_f is None and metar.get("temperature_c") is not None:
            temperature_f = metar["temperature_c"] * 9.0 / 5.0 + 32.0

        response = AirportWeather(
            airport=airport_data.get("icao") or code,
            conditions=conditions,
            temperature=float(temperature_f) if temperature_f is not None else 0.0,
            wind_speed=float(metar.get("wind_speed_kt") or 0.0),
            wind_direction=int(metar.get("wind_dir_degrees") or 0),
            visibility=float(metar.get("visibility_statute_mi") or 0.0),
            ceiling=ceiling_ft,
            metar=metar.get("raw_text") or "",
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_airport_weather: {e}")
        raise HTTPException(
            status_code=500,
            detail="Airport weather service temporarily unavailable",
        )


def _build_weather_response(weather_data: Dict[str, Any], request: WeatherRequest) -> WeatherResponse:
    """
    Normalize raw weather data from the model layer into the WeatherResponse schema.
    
    This function is intentionally defensive: it accepts both the structure returned by
    app.models.weather_async (location/current/forecast/overlays) and simpler mocked
    structures used in tests, and fills in reasonable defaults when data is missing.
    """
    # Coordinates
    location = weather_data.get("location", {}) or {}
    coordinates = Coordinates(
        latitude=location.get("latitude", request.lat),
        longitude=location.get("longitude", request.lon),
    )

    # Timezone (Open-Meteo usually provides one, otherwise fall back to UTC)
    timezone_str = weather_data.get("timezone") or "UTC"

    # Build forecast list
    raw_forecast: List[Dict[str, Any]] = weather_data.get("forecast") or []
    forecast_items: List[WeatherData] = []

    if raw_forecast:
        for item in raw_forecast:
            # Determine datetime
            ts = item.get("datetime") or item.get("date") or item.get("time")
            dt_value: datetime
            try:
                if isinstance(ts, (int, float)):
                    dt_value = datetime.fromtimestamp(ts, tz=timezone.utc)
                elif isinstance(ts, str):
                    # Allow either full ISO strings or date-only strings
                    try:
                        dt_value = datetime.fromisoformat(ts)
                    except ValueError:
                        dt_value = datetime.now(tz=timezone.utc)
                elif isinstance(ts, datetime):
                    dt_value = ts
                else:
                    dt_value = datetime.now(tz=timezone.utc)
            except Exception:
                dt_value = datetime.now(tz=timezone.utc)

            # Map common keys with safe fallbacks
            temperature = _safe_float(
                item.get("temperature"),
                item.get("temp_max"),
                default=0.0,
            )
            humidity = _safe_int(item.get("humidity"), default=50)
            wind_speed = _safe_float(
                item.get("wind_speed"),
                item.get("windspeed_max"),
                default=0.0,
            )
            wind_direction = _safe_int(
                item.get("wind_direction"),
                item.get("winddirection"),
                default=0,
            )
            pressure = _safe_float(item.get("pressure"), default=1013.25)

            visibility = item.get("visibility")
            precipitation = item.get("precipitation") or item.get("precipitation_sum")
            cloud_cover = item.get("cloud_cover") or item.get("clouds")
            weather_code = item.get("weather_code") or item.get("weathercode")
            description = item.get("weather_description") or item.get("description")

            forecast_items.append(
                WeatherData(
                    datetime=dt_value,
                    temperature=temperature,
                    humidity=humidity,
                    wind_speed=wind_speed,
                    wind_direction=wind_direction,
                    pressure=pressure,
                    visibility=visibility,
                    precipitation=precipitation,
                    cloud_cover=cloud_cover,
                    weather_code=weather_code,
                    weather_description=description,
                )
            )
    else:
        # Fallback to a single forecast entry based on "current" data if available
        current = weather_data.get("current", {}) or {}
        ts = current.get("time")
        try:
            if isinstance(ts, (int, float)):
                dt_value = datetime.fromtimestamp(ts, tz=timezone.utc)
            else:
                dt_value = datetime.now(tz=timezone.utc)
        except Exception:
            dt_value = datetime.now(tz=timezone.utc)

        forecast_items.append(
            WeatherData(
                datetime=dt_value,
                temperature=_safe_float(current.get("temperature"), default=0.0),
                humidity=_safe_int(current.get("humidity"), default=50),
                wind_speed=_safe_float(current.get("windspeed") or current.get("wind_speed"), default=0.0),
                wind_direction=_safe_int(current.get("winddirection") or current.get("wind_direction"), default=0),
                pressure=_safe_float(current.get("pressure"), default=1013.25),
                visibility=current.get("visibility"),
                precipitation=None,
                cloud_cover=current.get("clouds"),
                weather_code=current.get("weathercode"),
                weather_description=current.get("description"),
            )
        )

    metadata: Dict[str, Any] = {
        "source": weather_data.get("source", "combined"),
        "has_overlays": bool(weather_data.get("overlays")),
    }

    return WeatherResponse(
        coordinates=coordinates,
        timezone=timezone_str,
        forecast=forecast_items,
        metadata=metadata,
    )


def _safe_float(*values: Any, default: float = 0.0) -> float:
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return float(default)


def _safe_int(*values: Any, default: int = 0) -> int:
    for value in values:
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return int(default)


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