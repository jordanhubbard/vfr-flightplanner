"""
FastAPI Application Factory.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import Settings
from app.schemas import ErrorResponse


# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting VFR Flight Planner API...")
    
    # Initialize any required services here
    # - Database connections
    # - Cache initialization
    # - External API health checks
    
    yield
    
    # Shutdown
    logger.info("Shutting down VFR Flight Planner API...")
    
    # Cleanup any resources here
    # - Close database connections
    # - Clear caches
    # - Close external connections


def create_app(settings: Settings) -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="""
        ## VFR Flight Planner API

        A comprehensive **Visual Flight Rules (VFR)** flight planning API with advanced weather integration 
        and route optimization capabilities.

        ### Features

        * **🗺️ Route Planning**: Advanced VFR route planning with fuel stops and terrain avoidance
        * **🌤️ Weather Integration**: Real-time weather data from multiple sources (OpenWeatherMap, Open-Meteo)
        * **✈️ Airport Information**: Comprehensive airport database with METAR weather reports
        * **⛽ Fuel Planning**: Intelligent fuel planning with reserve calculations
        * **📊 Performance Monitoring**: Built-in health checks and API monitoring
        * **🔒 Security**: Rate limiting, CORS protection, and security headers

        ### Data Sources

        - **Open-Meteo**: Free weather API for global forecasts
        - **OpenWeatherMap**: Professional weather data (API key required for enhanced features)
        - **OurAirports**: Comprehensive global airport database

        ### Getting Started

        1. Explore the endpoints below
        2. Check `/api/health` for system status
        3. Use `/api/airports` to find nearby airports
        4. Plan routes with `/api/plan_route`
        5. Get weather data with `/api/weather`
        """,
        version=settings.app_version,
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
        debug=settings.debug,
        contact={
            "name": "VFR Flight Planner",
            "url": "https://github.com/your-org/vfr-flightplanner",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )
    
    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add middleware
    add_middleware(app, settings)
    
    # Add exception handlers
    add_exception_handlers(app)
    
    # Register routers
    register_routers(app, settings)
    
    logger.info(f"FastAPI application created successfully in {'debug' if settings.debug else 'production'} mode")
    
    return app


def add_middleware(app: FastAPI, settings: Settings) -> None:
    """Add middleware to FastAPI app."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    # Trusted host middleware for production
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure appropriately for production
        )
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response


def add_exception_handlers(app: FastAPI) -> None:
    """Add custom exception handlers."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="ValidationError",
                message="Invalid request data",
                details={"errors": exc.errors()}
            ).dict(),
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="HTTPException",
                message=exc.detail,
                details={"status_code": exc.status_code}
            ).dict(),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
                details={"type": type(exc).__name__}
            ).dict(),
        )


def register_routers(app: FastAPI, settings: Settings) -> None:
    """Register API routers."""
    
    # Import routers (will be created next)
    from app.routers import health, weather, airport, flight_plan, main
    
    # Register API routers with prefix
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(weather.router, prefix=settings.api_prefix, tags=["weather"])
    app.include_router(airport.router, prefix=settings.api_prefix, tags=["airport"])
    app.include_router(flight_plan.router, prefix=settings.api_prefix, tags=["flight-plan"])
    
    # Register main router (for web interface)
    app.include_router(main.router, tags=["main"])


# For compatibility during migration
def create_app_legacy(config_class=None):
    """Legacy function for backward compatibility."""
    from app.config import settings
    return create_app(settings)
