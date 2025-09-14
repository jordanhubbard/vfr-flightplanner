"""
Health Check API Pydantic schemas.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ServiceHealth(BaseModel):
    """Individual service health status."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": True,
                "error": None,
                "timestamp": "2023-12-01T12:00:00Z",
                "response_time_ms": 150.5,
                "api_calls": 42
            }
        }
    )
    
    status: bool = Field(..., description="Service health status")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    timestamp: datetime = Field(..., description="Last check timestamp")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    api_calls: Optional[int] = Field(None, description="Number of API calls made")


class HealthResponse(BaseModel):
    """Complete health check response schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_status": "operational",
                "services": {
                    "openweathermap": {
                        "status": True,
                        "error": None,
                        "timestamp": "2023-12-01T12:00:00Z",
                        "response_time_ms": 150.5,
                        "api_calls": 42
                    },
                    "openmeteo": {
                        "status": True,
                        "error": None,
                        "timestamp": "2023-12-01T12:00:00Z",
                        "response_time_ms": 89.2,
                        "api_calls": 0
                    }
                },
                "timestamp": "2023-12-01T12:00:00Z",
                "uptime_seconds": 3600.0,
                "version": "1.0.0"
            }
        }
    )
    
    overall_status: str = Field(..., description="Overall system health status")
    services: Dict[str, ServiceHealth] = Field(..., description="Individual service health statuses")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="System uptime in seconds")
    version: Optional[str] = Field(None, description="Application version")


class CacheStatusResponse(BaseModel):
    """Airport cache status response schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cache_file": "app/models/airports_cache.json",
                "cache_size": 45632,
                "last_updated": "2023-12-01T06:00:00Z",
                "file_size_bytes": 15728640,
                "is_valid": True
            }
        } 
    )
    
    cache_file: str = Field(..., description="Cache file path")
    cache_size: int = Field(..., description="Number of cached airports")
    last_updated: datetime = Field(..., description="Last cache update timestamp")
    file_size_bytes: int = Field(..., description="Cache file size in bytes")
    is_valid: bool = Field(..., description="Cache validity status") 