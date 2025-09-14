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
from fastapi.staticfiles import StaticFiles
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
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
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
            ).model_dump(mode='json'),
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
            ).model_dump(mode='json'),
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
            ).model_dump(mode='json'),
        )


def register_routers(app: FastAPI, settings: Settings) -> None:
    """Register API routers."""
    
    # Import routers
    from app.routers import health, weather, airport, flight_plan, main
    
    # Register API routers with prefix
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(weather.router, prefix=settings.api_prefix, tags=["weather"])
    app.include_router(airport.router, prefix=settings.api_prefix, tags=["airport"])
    app.include_router(flight_plan.router, prefix=settings.api_prefix, tags=["flight-plan"])
    
    # Register main router (for web interface)
    app.include_router(main.router, tags=["main"])
    
    # Add React frontend serving
    add_react_routes(app, settings)


def add_react_routes(app: FastAPI, settings: Settings) -> None:
    """Add routes for serving React frontend."""
    from pathlib import Path
    from fastapi.responses import HTMLResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles
    import os
    
    # Mount static files for React build
    static_path = Path(__file__).parent / "static"
    static_path.mkdir(exist_ok=True)
    
    # Mount the frontend dist directory
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
        
        # Serve React app for all non-API routes
        @app.get("/", response_class=HTMLResponse)
        async def serve_react_app():
            """Serve the React application."""
            # In development mode, return API info instead of serving React
            if os.environ.get('ENVIRONMENT') == 'development':
                return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>VFR Flight Planner API - Development Mode</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .api-link {{ display: inline-block; margin: 10px 0; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                        .api-link:hover {{ background: #0056b3; }}
                        .dev-info {{ background: #e7f3ff; padding: 15px; border-radius: 4px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>✈️ VFR Flight Planner API</h1>
                        <div class="dev-info">
                            <strong>Development Mode Active</strong><br>
                            FastAPI backend running on port 8080
                        </div>
                        <h2>API Documentation</h2>
                        <a href="/api/docs" class="api-link">📚 Interactive API Docs (Swagger)</a><br>
                        <a href="/api/redoc" class="api-link">📖 ReDoc Documentation</a><br>
                        <a href="/api/health" class="api-link">❤️ Health Check</a>
                        
                        <h2>Quick Test</h2>
                        <p>Get weather: <code>GET /api/weather/KPAO</code></p>
                        <p>Search airports: <code>GET /api/airports/search?q=palo+alto</code></p>
                    </div>
                </body>
                </html>
                """)
            
            # Production mode: serve built React app
            try:
                index_file = frontend_dist / "index.html"
                if index_file.exists():
                    with open(index_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
                else:
                    return HTMLResponse(content=f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>VFR Flight Planner</title>
                    </head>
                    <body>
                        <h1>VFR Flight Planner</h1>
                        <p>React build not found at: <code>{index_file}</code></p>
                        <p>Please build the frontend:</p>
                        <pre>cd frontend && npm run build</pre>
                    </body>
                    </html>
                    """)
            except Exception as e:
                return HTMLResponse(content=f"<h1>Error serving frontend: {e}</h1>", status_code=500)
        
        # API Documentation routes
        @app.get("/docs", response_class=HTMLResponse)
        async def api_docs_redirect():
            """Redirect to API documentation."""
            return RedirectResponse(url="/api/docs", status_code=302)

        @app.get("/api-docs", response_class=HTMLResponse) 
        async def api_docs_alt():
            """Alternative API documentation endpoint."""
            return RedirectResponse(url="/api/docs", status_code=302)
        
        # Catch-all route for React SPA (must be last!)
        @app.get("/{path:path}", response_class=HTMLResponse)
        async def serve_spa(path: str):
            """Serve React SPA for all routes (client-side routing)."""
            # Don't serve SPA for API routes - let them return proper 404
            if path.startswith("api/"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="API endpoint not found")
            
            return await serve_react_app()
    else:
        # No React build found - serve basic info page
        @app.get("/", response_class=HTMLResponse)
        async def serve_basic_info():
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>VFR Flight Planner API</title>
            </head>
            <body>
                <h1>VFR Flight Planner API</h1>
                <p>Frontend not built. Build with: <code>cd frontend && npm run build</code></p>
                <p><a href="/api/docs">API Documentation</a></p>
            </body>
            </html>
            """)


# Create the application instance
from app.config import settings

app = create_app(settings)
