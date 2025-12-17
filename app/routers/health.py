"""
Health Check Router.

Provides endpoints for system health monitoring and cache status.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from app.config import Settings, settings
from app.schemas import HealthResponse, CacheStatusResponse, ServiceHealth, SuccessResponse
from app.utils.api_helpers import check_owm_api, check_meteo_api

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/health", response_model=HealthResponse)
@limiter.limit("10/minute")
async def health_check(request: Request) -> HealthResponse:
    """
    Check the health of all required external APIs and services.
    
    Returns:
        HealthResponse: Overall system health status
    """
    try:
        # Check external APIs concurrently
        owm_task = asyncio.create_task(_check_owm_api())
        meteo_task = asyncio.create_task(_check_meteo_api())
        
        # Wait for all checks to complete
        owm_result, meteo_result = await asyncio.gather(
            owm_task, meteo_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(owm_result, Exception):
            logger.error(f"OWM API check failed: {owm_result}")
            owm_result = ServiceHealth(
                status=False,
                error="Network connectivity issues",
                timestamp=datetime.now(),
                api_calls=0
            )
        
        if isinstance(meteo_result, Exception):
            logger.error(f"Meteo API check failed: {meteo_result}")
            meteo_result = ServiceHealth(
                status=False,
                error="Network connectivity issues",
                timestamp=datetime.now()
            )
        
        # Determine overall status
        services = {
            "openweathermap": owm_result,
            "openmeteo": meteo_result
        }
        
        overall_status = "operational"
        if not any(service.status for service in services.values()):
            overall_status = "degraded"
        elif not all(service.status for service in services.values()):
            overall_status = "partial"
        
        return HealthResponse(
            overall_status=overall_status,
            services=services,
            version=settings.app_version,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )


@router.get("/airport-cache-status")
@limiter.limit("5/minute")
async def airport_cache_status(request: Request) -> Dict[str, Any]:
    """
    Get the status of the airport cache.
    
    Returns:
        Dict: Cache status information with overall_status field
    """
    try:
        import os
        import json
        from datetime import datetime
        
        cache_file = settings.airport_cache_file
        
        if not os.path.exists(cache_file):
            logger.warning(f"Airport cache file not found: {cache_file}")
            return {
                "overall_status": "missing",
                "airport_cache": {
                    "cache_file": cache_file,
                    "exists": False,
                    "airport_count": 0,
                    "message": "Airport cache needs to be downloaded. Click refresh to download."
                }
            }
        
        # Get file stats
        stat = os.stat(cache_file)
        file_size = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        
        # Load cache to get size
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                cache_size = len(cache_data) if isinstance(cache_data, list) else 0
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid cache file format: {e}")
            cache_size = 0
        
        is_valid = cache_size > 0 and file_size > 100
        overall_status = "ready" if is_valid else "invalid"
        
        return {
            "overall_status": overall_status,
            "airport_cache": {
                "cache_file": cache_file,
                "exists": True,
                "airport_count": cache_size,
                "last_updated": last_modified.isoformat(),
                "file_size_bytes": file_size,
                "is_valid": is_valid
            }
        }
        
    except Exception as e:
        logger.error(f"Cache status check failed: {e}")
        return {
            "overall_status": "error",
            "airport_cache": {
                "exists": False,
                "error": str(e)
            }
        }


@router.post("/refresh-airport-cache", response_model=SuccessResponse)
@limiter.limit("1/hour")
async def refresh_airport_cache(request: Request) -> SuccessResponse:
    """
    Refresh the airport cache by downloading from OpenAIP.
    
    Returns:
        SuccessResponse: Cache refresh confirmation
    """
    try:
        import subprocess
        import os
        
        logger.info("Airport cache refresh requested")
        
        # Run the update_airport_cache script
        script_path = os.path.join(os.path.dirname(__file__), '../../scripts/update_airport_cache.py')
        result = await asyncio.to_thread(
            subprocess.run,
            ['python3', script_path, '--force'],
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Airport cache refreshed successfully: {result.stdout}")
            return SuccessResponse(
                message="Airport cache refreshed successfully"
            )
        else:
            logger.error(f"Airport cache refresh failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Airport cache refresh failed: {result.stderr}"
            )
        
    except subprocess.TimeoutExpired:
        logger.error("Airport cache refresh timed out")
        raise HTTPException(
            status_code=504,
            detail="Airport cache refresh timed out"
        )
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh cache: {str(e)}"
        )


async def _check_owm_api() -> ServiceHealth:
    """Check OpenWeatherMap API health."""
    try:
        start_time = datetime.now()
        result = await asyncio.to_thread(check_owm_api)
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds() * 1000
        
        return ServiceHealth(
            status=result.get('status', False),
            error=result.get('error'),
            timestamp=datetime.now(),
            response_time_ms=response_time,
            api_calls=result.get('api_calls', 0)
        )
    except Exception as e:
        return ServiceHealth(
            status=False,
            error=str(e),
            timestamp=datetime.now(),
            api_calls=0
        )


async def _check_meteo_api() -> ServiceHealth:
    """Check Open-Meteo API health."""
    try:
        start_time = datetime.now()
        result = await asyncio.to_thread(check_meteo_api)
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds() * 1000
        
        return ServiceHealth(
            status=result.get('status', False),
            error=result.get('error'),
            timestamp=datetime.now(),
            response_time_ms=response_time,
            api_calls=0
        )
    except Exception as e:
        return ServiceHealth(
            status=False,
            error=str(e),
            timestamp=datetime.now(),
            api_calls=0
        ) 