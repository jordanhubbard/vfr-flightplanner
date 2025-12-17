"""
FastAPI Application Configuration using Pydantic Settings.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # Application settings
    app_name: str = Field("VFR Flight Planner", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    
    # Server settings
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(False, description="Auto-reload on code changes")
    
    # API settings
    api_prefix: str = Field("/api", description="API prefix")
    openapi_url: str = Field("/openapi.json", description="OpenAPI JSON endpoint")
    docs_url: str = Field("/docs", description="Swagger UI endpoint")
    redoc_url: str = Field("/redoc", description="ReDoc endpoint")
    
    # CORS settings
    cors_origins: List[str] = Field(["*"], description="Allowed CORS origins")
    cors_methods: List[str] = Field(["*"], description="Allowed CORS methods")
    cors_headers: List[str] = Field(["*"], description="Allowed CORS headers")
    
    # Rate limiting
    rate_limit_calls: int = Field(100, description="Rate limit calls per minute")
    rate_limit_period: int = Field(60, description="Rate limit period in seconds")
    
    # External API settings
    openweather_api_key: Optional[str] = Field(None, description="OpenWeatherMap API key")
    openweather_base_url: str = Field("https://api.openweathermap.org/data/2.5", description="OpenWeatherMap base URL")
    openmeteo_base_url: str = Field("https://api.open-meteo.com/v1", description="Open-Meteo base URL")
    
    # Cache settings
    cache_enabled: bool = Field(True, description="Enable caching")
    cache_ttl: int = Field(300, description="Cache TTL in seconds")
    redis_url: Optional[str] = Field(None, description="Redis URL for caching")
    
    # Database settings (for future use)
    database_url: Optional[str] = Field(None, description="Database URL")
    
    # Logging settings
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    
    # Security settings
    secret_key: str = Field("your-secret-key-here", description="Secret key for signing")
    access_token_expire_minutes: int = Field(30, description="Access token expiration in minutes")
    
    # File paths
    airport_cache_file: str = Field("/app/data/airports_cache.json", description="Airport cache file path")
    logs_directory: str = Field("logs", description="Logs directory")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development environment settings."""
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"
    
    class Config:
        env_file = ".env.development"


class ProductionSettings(Settings):
    """Production environment settings."""
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"
    cors_origins: List[str] = []  # Restrict CORS in production
    
    class Config:
        env_file = ".env.production"


class TestingSettings(Settings):
    """Testing environment settings."""
    debug: bool = True
    log_level: str = "WARNING"
    cache_enabled: bool = False
    
    class Config:
        env_file = ".env.testing"


def get_settings() -> Settings:
    """Get application settings based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()
