"""
Flight Planning Router.

Provides endpoints for VFR route planning, optimization, and flight plan generation.
"""

import asyncio
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Body
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas import FlightPlanRequest, FlightPlanResponse
from app.models.flight_planner import plan_route

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/plan_route", response_model=FlightPlanResponse)
@limiter.limit("10/minute")
async def plan_vfr_route(
    request,
    flight_request: FlightPlanRequest = Body(..., description="Flight plan request")
) -> FlightPlanResponse:
    """
    Plan a VFR route between two airports with advanced fuel planning, terrain avoidance, and wind analysis.
    
    Args:
        flight_request: Flight planning parameters
        
    Returns:
        FlightPlanResponse: Complete flight plan with route, fuel planning, and weather analysis
        
    Raises:
        HTTPException: If flight planning fails
    """
    try:
        logger.info(f"Flight planning request: {flight_request.start_code} -> {flight_request.end_code}")
        
        # Plan the route asynchronously
        route_data = await asyncio.to_thread(
            plan_route,
            flight_request.start_code,
            flight_request.end_code,
            flight_request.aircraft_range_nm,
            flight_request.groundspeed_kt,
            flight_request.fuel_capacity_gal,
            flight_request.fuel_burn_gph,
            flight_request.avoid_terrain,
            flight_request.plan_fuel_stops,
            flight_request.cruising_altitude_ft
        )
        
        if not route_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate flight plan"
            )
        
        # Check for errors in the route planning
        if 'error' in route_data:
            raise HTTPException(
                status_code=400,
                detail=route_data['error']
            )
        
        # Transform the route data to match our response schema
        response_data = _transform_route_data(route_data, flight_request)
        
        return FlightPlanResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in plan_vfr_route: {e}")
        raise HTTPException(
            status_code=500,
            detail="Flight planning service temporarily unavailable"
        )


def _transform_route_data(route_data: Dict[str, Any], flight_request: FlightPlanRequest) -> Dict[str, Any]:
    """
    Transform route data from the flight planner to match the response schema.
    
    Args:
        route_data: Raw route data from the flight planner
        flight_request: Original flight request
        
    Returns:
        Dict[str, Any]: Transformed data matching FlightPlanResponse schema
    """
    # Build route summary
    route_summary = {
        "departure": flight_request.start_code,
        "destination": flight_request.end_code,
        "total_legs": len(route_data.get('legs', [])),
        "fuel_stops": len(route_data.get('fuel_planning', {}).get('fuel_stops', []))
    }
    
    # Transform legs to match schema
    legs = []
    for leg in route_data.get('legs', []):
        leg_data = {
            "from_airport": leg.get('from', ''),
            "to_airport": leg.get('to', ''),
            "distance_nm": leg.get('distance_nm', 0),
            "cruise_altitude_ft": leg.get('cruise_altitude_ft', flight_request.cruising_altitude_ft),
            "estimated_time_hr": leg.get('estimated_time_hr', 0),
            "magnetic_heading": leg.get('magnetic_heading'),
            "true_heading": leg.get('true_heading'),
            "wind_component": leg.get('wind_component')
        }
        legs.append(leg_data)
    
    # Transform fuel planning if available
    fuel_planning = None
    if 'fuel_planning' in route_data and route_data['fuel_planning']:
        fuel_stops = []
        for stop in route_data['fuel_planning'].get('fuel_stops', []):
            fuel_stop = {
                "icao": stop.get('icao', ''),
                "name": stop.get('name', ''),
                "fuel_burn_gal": stop.get('fuel_burn_gal', 0),
                "total_fuel_burn_gal": stop.get('total_fuel_burn_gal', 0),
                "fuel_reserve_gal": stop.get('fuel_reserve_gal', 0),
                "coordinates": {
                    "latitude": stop.get('latitude', 0),
                    "longitude": stop.get('longitude', 0)
                }
            }
            fuel_stops.append(fuel_stop)
        
        fuel_planning = {
            "total_fuel_burn_gal": route_data['fuel_planning'].get('total_fuel_burn_gal', 0),
            "fuel_stops": fuel_stops,
            "reserve_fuel_gal": flight_request.fuel_capacity_gal * 0.25,  # 25% reserve
            "total_fuel_required_gal": route_data['fuel_planning'].get('total_fuel_burn_gal', 0) * 1.25
        }
    
    # Add weather analysis (placeholder for now)
    weather_analysis = {
        "overall_conditions": "VFR conditions expected",
        "significant_weather": [],
        "wind_analysis": {
            "average_headwind": 0,
            "max_crosswind": 0,
            "favorable_altitudes": [flight_request.cruising_altitude_ft]
        },
        "visibility_forecast": {
            "minimum_visibility": 10.0,
            "areas_of_concern": []
        }
    }
    
    # Collect any warnings
    warnings = []
    if flight_request.avoid_terrain:
        warnings.append("Terrain avoidance routing enabled - may result in longer routes")
    
    return {
        "route_summary": route_summary,
        "legs": legs,
        "total_distance_nm": route_data.get('total_distance_nm', 0),
        "estimated_time_hr": route_data.get('estimated_time_hr', 0),
        "fuel_planning": fuel_planning,
        "weather_analysis": weather_analysis,
        "alternate_routes": None,  # Could be added in future
        "warnings": warnings
    }


# Additional flight planning endpoints can be added here
# Examples:
# - Flight plan filing
# - Route optimization
# - Alternate airport recommendations
# - Performance calculations
# - Weight and balance calculations 