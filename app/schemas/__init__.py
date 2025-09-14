"""
FastAPI Pydantic schemas for request/response validation.
"""

from .weather import WeatherRequest, WeatherResponse, AreaForecastRequest
from .airport import AirportRequest, AirportResponse, AirportSearchRequest, AirportSearchResponse, AirportInfo, MetarRequest, MetarResponse
from .flight_plan import FlightPlanRequest, FlightPlanResponse
from .health import HealthResponse, CacheStatusResponse, ServiceHealth
from .common import ErrorResponse, SuccessResponse

__all__ = [
    "WeatherRequest",
    "WeatherResponse",
    "AreaForecastRequest",
    "AirportRequest",
    "AirportResponse",
    "AirportSearchRequest",
    "AirportSearchResponse",
    "AirportInfo",
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