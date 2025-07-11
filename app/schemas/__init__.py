"""
FastAPI Pydantic schemas for request/response validation.
"""

from .weather import WeatherRequest, WeatherResponse, AreaForecastRequest
from .airport import AirportRequest, AirportResponse, AirportSearchRequest, MetarRequest, MetarResponse
from .flight_plan import FlightPlanRequest, FlightPlanResponse
from .health import HealthResponse, CacheStatusResponse
from .common import ErrorResponse, SuccessResponse

__all__ = [
    "WeatherRequest",
    "WeatherResponse",
    "AreaForecastRequest",
    "AirportRequest",
    "AirportResponse",
    "AirportSearchRequest",
    "MetarRequest",
    "MetarResponse",
    "FlightPlanRequest",
    "FlightPlanResponse",
    "HealthResponse",
    "CacheStatusResponse",
    "ErrorResponse",
    "SuccessResponse"
] 