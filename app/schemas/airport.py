"""
Airport API Pydantic schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .common import Coordinates


class AirportSearchRequest(BaseModel):
    """Airport search request schema."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    radius: int = Field(50, ge=1, le=500, description="Search radius in nautical miles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 40.7128,
                "lon": -74.0060,
                "radius": 50
            }
        }


class AirportRequest(BaseModel):
    """Single airport lookup request schema."""
    code: str = Field(..., min_length=3, max_length=4, description="ICAO or IATA airport code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "KJFK"
            }
        }


class MetarData(BaseModel):
    """METAR weather data."""
    icao: str = Field(..., description="ICAO airport code")
    raw_text: str = Field(..., description="Raw METAR text")
    observation_time: Optional[datetime] = Field(None, description="Observation timestamp")
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    dewpoint: Optional[float] = Field(None, description="Dewpoint in Celsius")
    wind_speed: Optional[float] = Field(None, description="Wind speed in knots")
    wind_direction: Optional[int] = Field(None, description="Wind direction in degrees")
    wind_gust: Optional[float] = Field(None, description="Wind gust in knots")
    visibility: Optional[float] = Field(None, description="Visibility in statute miles")
    altimeter: Optional[float] = Field(None, description="Altimeter setting in inHg")
    sky_conditions: List[str] = Field(default_factory=list, description="Sky condition reports")
    weather_phenomena: List[str] = Field(default_factory=list, description="Weather phenomena")
    
    class Config:
        json_schema_extra = {
            "example": {
                "icao": "KJFK",
                "raw_text": "KJFK 011251Z 27008KT 10SM FEW250 15/M07 A3012 RMK AO2 SLP221 T01501067",
                "observation_time": "2023-12-01T12:51:00Z",
                "temperature": 15.0,
                "dewpoint": -6.7,
                "wind_speed": 8.0,
                "wind_direction": 270,
                "visibility": 10.0,
                "altimeter": 30.12,
                "sky_conditions": ["FEW250"],
                "weather_phenomena": []
            }
        }


class AirportInfo(BaseModel):
    """Airport information schema."""
    icao: str = Field(..., description="ICAO airport code")
    iata: Optional[str] = Field(None, description="IATA airport code")
    name: str = Field(..., description="Airport name")
    coordinates: Coordinates = Field(..., description="Airport coordinates")
    elevation: Optional[float] = Field(None, description="Airport elevation in feet")
    country: Optional[str] = Field(None, description="Country code")
    region: Optional[str] = Field(None, description="Region/state")
    municipality: Optional[str] = Field(None, description="Municipality")
    airport_type: Optional[str] = Field(None, description="Airport type")
    runways: Optional[List[Dict[str, Any]]] = Field(None, description="Runway information")
    frequencies: Optional[List[Dict[str, Any]]] = Field(None, description="Radio frequencies")
    weather: Optional[MetarData] = Field(None, description="Current weather data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "icao": "KJFK",
                "iata": "JFK",
                "name": "John F Kennedy International Airport",
                "coordinates": {
                    "latitude": 40.6398,
                    "longitude": -73.7789
                },
                "elevation": 13.0,
                "country": "US",
                "region": "NY",
                "municipality": "New York",
                "airport_type": "large_airport",
                "runways": [
                    {
                        "length_ft": 14511,
                        "width_ft": 200,
                        "surface": "concrete",
                        "le_ident": "04L",
                        "he_ident": "22R"
                    }
                ],
                "frequencies": [
                    {
                        "type": "ATIS",
                        "frequency": "128.725",
                        "description": "ATIS"
                    }
                ]
            }
        }


class AirportResponse(BaseModel):
    """Single airport response schema."""
    airport: AirportInfo = Field(..., description="Airport information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "airport": {
                    "icao": "KJFK",
                    "iata": "JFK",
                    "name": "John F Kennedy International Airport",
                    "coordinates": {
                        "latitude": 40.6398,
                        "longitude": -73.7789
                    },
                    "elevation": 13.0,
                    "country": "US",
                    "region": "NY",
                    "municipality": "New York",
                    "airport_type": "large_airport"
                }
            }
        }


class AirportSearchResponse(BaseModel):
    """Airport search response schema."""
    search_center: Coordinates = Field(..., description="Search center coordinates")
    radius_nm: int = Field(..., description="Search radius in nautical miles")
    airports: List[AirportInfo] = Field(..., description="List of airports found")
    count: int = Field(..., description="Number of airports found")
    
    class Config:
        json_schema_extra = {
            "example": {
                "search_center": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                },
                "radius_nm": 50,
                "airports": [
                    {
                        "icao": "KJFK",
                        "iata": "JFK",
                        "name": "John F Kennedy International Airport",
                        "coordinates": {
                            "latitude": 40.6398,
                            "longitude": -73.7789
                        },
                        "elevation": 13.0,
                        "country": "US",
                        "region": "NY",
                        "municipality": "New York",
                        "airport_type": "large_airport"
                    }
                ],
                "count": 1
            }
        }


class AirportBasic(BaseModel):
    """Flattened airport schema tailored for the React frontend."""

    icao: str = Field(..., description="ICAO airport code")
    iata: Optional[str] = Field(None, description="IATA airport code")
    name: str = Field(..., description="Airport name")
    city: Optional[str] = Field(None, description="City or locality")
    country: Optional[str] = Field(None, description="Country code")
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    elevation: Optional[float] = Field(None, description="Airport elevation in feet")
    type: Optional[str] = Field(None, description="Airport type")


class MetarRequest(BaseModel):
    """METAR data request schema."""
    codes: List[str] = Field(..., description="List of ICAO airport codes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "codes": ["KJFK", "KLGA", "KEWR"]
            }
        }


class MetarResponse(BaseModel):
    """METAR data response schema."""
    metar_data: Dict[str, MetarData] = Field(..., description="METAR data by ICAO code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metar_data": {
                    "KJFK": {
                        "icao": "KJFK",
                        "raw_text": "KJFK 011251Z 27008KT 10SM FEW250 15/M07 A3012 RMK AO2 SLP221 T01501067",
                        "observation_time": "2023-12-01T12:51:00Z",
                        "temperature": 15.0,
                        "dewpoint": -6.7,
                        "wind_speed": 8.0,
                        "wind_direction": 270,
                        "visibility": 10.0,
                        "altimeter": 30.12,
                        "sky_conditions": ["FEW250"],
                        "weather_phenomena": []
                    }
                },
                "timestamp": "2023-12-01T12:55:00Z"
            }
        } 