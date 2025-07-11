"""
Airport Router.

Provides endpoints for airport information, search, and METAR data.
"""

import asyncio
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Body, Query
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import (
    AirportSearchRequest, AirportSearchResponse, AirportResponse, 
    MetarRequest, MetarResponse, AirportInfo
)
from app.models.airport import get_airports, get_airport_coordinates, get_metar_data

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/airports", response_model=AirportSearchResponse)
@limiter.limit("20/minute")
async def search_airports(
    request,
    search_request: AirportSearchRequest = Body(..., description="Airport search request")
) -> AirportSearchResponse:
    """
    Search for airports within a radius of a location.
    
    Args:
        search_request: Airport search parameters
        
    Returns:
        AirportSearchResponse: List of airports found
        
    Raises:
        HTTPException: If airport search fails
    """
    try:
        logger.info(f"Airport search request: {search_request.lat}, {search_request.lon}, radius: {search_request.radius}")
        
        # Get airports from the airport model asynchronously
        airports_data = await asyncio.to_thread(
            get_airports,
            search_request.lat,
            search_request.lon,
            search_request.radius
        )
        
        if not airports_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch airport data"
            )
        
        # Get METAR data for all airports with ICAO codes
        airports_list = airports_data.get('airports', [])
        icao_codes = [airport['icao'] for airport in airports_list if airport.get('icao')]
        
        metar_data = {}
        if icao_codes:
            try:
                metar_data = await asyncio.to_thread(get_metar_data, icao_codes)
            except Exception as e:
                logger.warning(f"Failed to fetch METAR data: {e}")
        
        # Enhance airports with weather data
        enhanced_airports = []
        for airport in airports_list:
            airport_info = AirportInfo(**airport)
            if airport.get('icao') in metar_data:
                airport_info.weather = metar_data[airport['icao']]
            enhanced_airports.append(airport_info)
        
        return AirportSearchResponse(
            search_center={"latitude": search_request.lat, "longitude": search_request.lon},
            radius_nm=search_request.radius,
            airports=enhanced_airports,
            count=len(enhanced_airports)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_airports: {e}")
        raise HTTPException(
            status_code=500,
            detail="Airport search service temporarily unavailable"
        )


@router.get("/airport", response_model=AirportResponse)
@limiter.limit("30/minute")
async def get_airport_info(
    request,
    code: str = Query(..., description="Airport ICAO or IATA code", min_length=3, max_length=4)
) -> AirportResponse:
    """
    Get airport information by ICAO or IATA code.
    
    Args:
        code: Airport ICAO or IATA code
        
    Returns:
        AirportResponse: Airport information
        
    Raises:
        HTTPException: If airport is not found
    """
    try:
        code = code.strip().upper()
        logger.info(f"Airport lookup request for code: {code}")
        
        # Get airport coordinates from the airport model
        airport_data = await asyncio.to_thread(get_airport_coordinates, code)
        
        if not airport_data:
            raise HTTPException(
                status_code=404,
                detail=f"No airport found with code {code}"
            )
        
        # Convert to AirportInfo schema
        airport_info = AirportInfo(**airport_data)
        
        return AirportResponse(airport=airport_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_airport_info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Airport lookup service temporarily unavailable"
        )


@router.get("/metar", response_model=MetarResponse)
@limiter.limit("20/minute")
async def get_metar_weather(
    request,
    codes: str = Query(..., description="Comma-separated list of ICAO airport codes")
) -> MetarResponse:
    """
    Get METAR weather data for airports.
    
    Args:
        codes: Comma-separated list of ICAO airport codes
        
    Returns:
        MetarResponse: METAR weather data
        
    Raises:
        HTTPException: If METAR data cannot be retrieved
    """
    try:
        if not codes:
            raise HTTPException(
                status_code=400,
                detail="Airport codes are required"
            )
        
        # Split codes by comma and convert to uppercase
        icao_codes = [code.strip().upper() for code in codes.split(',')]
        
        logger.info(f"METAR request for codes: {icao_codes}")
        
        # Get METAR data from the airport model
        metar_data = await asyncio.to_thread(get_metar_data, icao_codes)
        
        if not metar_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch METAR data"
            )
        
        return MetarResponse(metar_data=metar_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_metar_weather: {e}")
        raise HTTPException(
            status_code=500,
            detail="METAR service temporarily unavailable"
        )


# Additional airport-related endpoints can be added here
# Examples:
# - Airport details with runway information
# - Airport frequencies
# - Airport NOTAMs
# - Nearby navigation aids 