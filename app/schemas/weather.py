"""
Weather API Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .common import Coordinates


class WeatherRequest(BaseModel):
    """Weather forecast request schema."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    days: int = Field(7, ge=1, le=14, description="Number of days for forecast")
    overlays: List[str] = Field(default_factory=list, description="Weather overlay types")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 40.7128,
                "lon": -74.0060,
                "days": 7,
                "overlays": ["wind", "precipitation", "clouds"]
            }
        }


class WeatherData(BaseModel):
    """Single weather data point."""
    datetime: datetime = Field(..., description="Forecast timestamp")
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    wind_direction: int = Field(..., ge=0, le=360, description="Wind direction in degrees")
    pressure: float = Field(..., description="Atmospheric pressure in hPa")
    visibility: Optional[float] = Field(None, description="Visibility in kilometers")
    precipitation: Optional[float] = Field(None, description="Precipitation in mm")
    cloud_cover: Optional[int] = Field(None, ge=0, le=100, description="Cloud cover percentage")
    weather_code: Optional[int] = Field(None, description="Weather condition code")
    weather_description: Optional[str] = Field(None, description="Weather description")


class WeatherResponse(BaseModel):
    """Weather forecast response schema."""
    coordinates: Coordinates = Field(..., description="Request coordinates")
    timezone: str = Field(..., description="Timezone identifier")
    forecast: List[WeatherData] = Field(..., description="Weather forecast data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "coordinates": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                },
                "timezone": "America/New_York",
                "forecast": [
                    {
                        "datetime": "2023-12-01T12:00:00Z",
                        "temperature": 15.5,
                        "humidity": 65,
                        "wind_speed": 3.2,
                        "wind_direction": 270,
                        "pressure": 1013.25,
                        "visibility": 10.0,
                        "precipitation": 0.0,
                        "cloud_cover": 25,
                        "weather_code": 1,
                        "weather_description": "Partly cloudy"
                    }
                ],
                "metadata": {
                    "source": "OpenWeatherMap",
                    "generated_at": "2023-12-01T10:30:00Z"
                }
            }
        }


class AreaForecastRequest(BaseModel):
    """Area forecast request schema."""
    bounds: Dict[str, float] = Field(..., description="Geographic bounds")
    resolution: Optional[str] = Field("medium", description="Forecast resolution")
    layers: List[str] = Field(default_factory=list, description="Weather layers to include")
    
    class Config:
        json_schema_extra = {
            "example": {
                "bounds": {
                    "north": 41.0,
                    "south": 40.0,
                    "east": -73.0,
                    "west": -75.0
                },
                "resolution": "medium",
                "layers": ["wind", "precipitation", "temperature"]
            }
        } 