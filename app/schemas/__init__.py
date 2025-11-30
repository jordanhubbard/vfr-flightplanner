"""
FastAPI Pydantic schemas for request/response validation.
"""

from .weather import WeatherRequest, WeatherResponse, AreaForecastRequest, WeatherData, AirportWeather
from .airport import (
    AirportRequest,
    AirportResponse,
    AirportSearchRequest,
    AirportSearchResponse,
    AirportInfo,
    MetarRequest,
    MetarResponse,
    AirportBasic,
)
from .flight_plan import FlightPlanRequest, FlightPlanResponse
from .health import HealthResponse, CacheStatusResponse, ServiceHealth
from .common import ErrorResponse, SuccessResponse

__all__ = [
    "WeatherRequest",
    "WeatherResponse",
    "WeatherData",
    "AirportWeather",
    "AreaForecastRequest",
    "AirportRequest",
    "AirportResponse",
    "AirportSearchRequest",
    "AirportSearchResponse",
    "AirportInfo",
    "AirportBasic",
    "MetarRequest",
    "MetarResponse",
    "FlightPlanRequest",
    "FlightPlanResponse",
    "HealthResponse",
    "CacheStatusResponse",
    "ServiceHealth",
    "ErrorResponse",
    "SuccessResponse"
] 