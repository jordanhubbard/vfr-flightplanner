"""
Flight Planning API Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .common import Coordinates


class FlightPlanRequest(BaseModel):
    """Flight plan request schema."""
    start_code: str = Field(..., min_length=3, max_length=4, description="Starting airport ICAO code")
    end_code: str = Field(..., min_length=3, max_length=4, description="Destination airport ICAO code")
    aircraft_range_nm: int = Field(..., ge=50, le=5000, description="Aircraft range in nautical miles")
    groundspeed_kt: int = Field(..., ge=50, le=500, description="Ground speed in knots")
    fuel_capacity_gal: float = Field(50.0, ge=1.0, le=1000.0, description="Aircraft fuel capacity in gallons")
    fuel_burn_gph: float = Field(12.0, ge=1.0, le=100.0, description="Fuel burn rate in gallons per hour")
    avoid_terrain: bool = Field(False, description="Whether to avoid high terrain routes")
    plan_fuel_stops: bool = Field(True, description="Whether to plan fuel stops with reserves")
    cruising_altitude_ft: int = Field(6500, ge=1000, le=17500, description="Planned cruising altitude in feet")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_code": "KJFK",
                "end_code": "KLAX",
                "aircraft_range_nm": 800,
                "groundspeed_kt": 140,
                "fuel_capacity_gal": 50.0,
                "fuel_burn_gph": 12.0,
                "avoid_terrain": False,
                "plan_fuel_stops": True,
                "cruising_altitude_ft": 6500
            }
        }


class FlightLeg(BaseModel):
    """Single flight leg schema."""
    from_airport: str = Field(..., description="Departure airport ICAO code")
    to_airport: str = Field(..., description="Arrival airport ICAO code")
    distance_nm: float = Field(..., ge=0, description="Distance in nautical miles")
    cruise_altitude_ft: int = Field(..., description="Cruise altitude in feet")
    estimated_time_hr: float = Field(..., ge=0, description="Estimated flight time in hours")
    magnetic_heading: Optional[int] = Field(None, ge=0, le=360, description="Magnetic heading in degrees")
    true_heading: Optional[int] = Field(None, ge=0, le=360, description="True heading in degrees")
    wind_component: Optional[Dict[str, float]] = Field(None, description="Wind component analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_airport": "KJFK",
                "to_airport": "KORD",
                "distance_nm": 740.5,
                "cruise_altitude_ft": 6500,
                "estimated_time_hr": 5.29,
                "magnetic_heading": 270,
                "true_heading": 275,
                "wind_component": {
                    "headwind": 10.5,
                    "crosswind": 5.2
                }
            }
        }


class FuelStop(BaseModel):
    """Fuel stop information schema."""
    icao: str = Field(..., description="Airport ICAO code")
    name: str = Field(..., description="Airport name")
    fuel_burn_gal: float = Field(..., ge=0, description="Fuel burn to reach this stop")
    total_fuel_burn_gal: float = Field(..., ge=0, description="Total fuel burn from start")
    fuel_reserve_gal: float = Field(..., ge=0, description="Fuel reserve remaining")
    coordinates: Coordinates = Field(..., description="Airport coordinates")
    
    class Config:
        json_schema_extra = {
            "example": {
                "icao": "KORD",
                "name": "Chicago O'Hare International Airport",
                "fuel_burn_gal": 38.5,
                "total_fuel_burn_gal": 38.5,
                "fuel_reserve_gal": 11.5,
                "coordinates": {
                    "latitude": 41.9786,
                    "longitude": -87.9048
                }
            }
        }


class FuelPlanning(BaseModel):
    """Fuel planning information schema."""
    total_fuel_burn_gal: float = Field(..., ge=0, description="Total fuel burn for entire route")
    fuel_stops: List[FuelStop] = Field(..., description="List of fuel stops")
    reserve_fuel_gal: float = Field(..., ge=0, description="Reserve fuel requirement")
    total_fuel_required_gal: float = Field(..., ge=0, description="Total fuel required including reserves")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_fuel_burn_gal": 85.2,
                "fuel_stops": [
                    {
                        "icao": "KORD",
                        "name": "Chicago O'Hare International Airport",
                        "fuel_burn_gal": 38.5,
                        "total_fuel_burn_gal": 38.5,
                        "fuel_reserve_gal": 11.5,
                        "coordinates": {
                            "latitude": 41.9786,
                            "longitude": -87.9048
                        }
                    }
                ],
                "reserve_fuel_gal": 12.0,
                "total_fuel_required_gal": 97.2
            }
        }


class WeatherAnalysis(BaseModel):
    """Weather analysis for flight route."""
    overall_conditions: str = Field(..., description="Overall weather conditions summary")
    significant_weather: List[str] = Field(default_factory=list, description="Significant weather along route")
    wind_analysis: Dict[str, Any] = Field(default_factory=dict, description="Wind analysis")
    visibility_forecast: Dict[str, Any] = Field(default_factory=dict, description="Visibility forecast")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_conditions": "VFR conditions expected",
                "significant_weather": ["Light rain showers near KORD", "Scattered thunderstorms west of KDEN"],
                "wind_analysis": {
                    "average_headwind": 8.5,
                    "max_crosswind": 12.3,
                    "favorable_altitudes": [6500, 8500]
                },
                "visibility_forecast": {
                    "minimum_visibility": 10.0,
                    "areas_of_concern": []
                }
            }
        }


class FlightPlanResponse(BaseModel):
    """Flight plan response schema."""
    route_summary: Dict[str, Any] = Field(..., description="Route summary information")
    legs: List[FlightLeg] = Field(..., description="Flight legs")
    total_distance_nm: float = Field(..., ge=0, description="Total distance in nautical miles")
    estimated_time_hr: float = Field(..., ge=0, description="Total estimated flight time in hours")
    fuel_planning: Optional[FuelPlanning] = Field(None, description="Fuel planning details")
    weather_analysis: Optional[WeatherAnalysis] = Field(None, description="Weather analysis")
    alternate_routes: Optional[List[Dict[str, Any]]] = Field(None, description="Alternative route options")
    warnings: List[str] = Field(default_factory=list, description="Route warnings and advisories")
    
    class Config:
        json_schema_extra = {
            "example": {
                "route_summary": {
                    "departure": "KJFK",
                    "destination": "KLAX",
                    "total_legs": 3,
                    "fuel_stops": 1
                },
                "legs": [
                    {
                        "from_airport": "KJFK",
                        "to_airport": "KORD",
                        "distance_nm": 740.5,
                        "cruise_altitude_ft": 6500,
                        "estimated_time_hr": 5.29,
                        "magnetic_heading": 270,
                        "true_heading": 275
                    }
                ],
                "total_distance_nm": 2445.8,
                "estimated_time_hr": 17.47,
                "fuel_planning": {
                    "total_fuel_burn_gal": 209.6,
                    "fuel_stops": [
                        {
                            "icao": "KORD",
                            "name": "Chicago O'Hare International Airport",
                            "fuel_burn_gal": 38.5,
                            "total_fuel_burn_gal": 38.5,
                            "fuel_reserve_gal": 11.5,
                            "coordinates": {
                                "latitude": 41.9786,
                                "longitude": -87.9048
                            }
                        }
                    ],
                    "reserve_fuel_gal": 12.0,
                    "total_fuel_required_gal": 221.6
                },
                "warnings": ["High terrain near KDEN", "Temporary flight restrictions in effect"]
            }
        } 