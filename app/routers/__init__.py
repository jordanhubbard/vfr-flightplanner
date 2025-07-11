"""
FastAPI Routers Package.

This package contains all the API route handlers organized by domain.
"""

from . import health, weather, airport, flight_plan, main

__all__ = [
    "health",
    "weather", 
    "airport",
    "flight_plan",
    "main"
] 