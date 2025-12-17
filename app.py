"""
VFR Flight Planner - Main Entry Point.

FastAPI application for VFR flight planning with weather integration.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import FastAPI app factory
from app import create_app
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = create_app(settings)

# Add static file mounting
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# For development with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting VFR Flight Planner on {settings.host}:{settings.port}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API documentation: http://{settings.host}:{settings.port}{settings.docs_url}")
    
    # Configure reload options for development
    reload_dirs = None
    reload_includes = None
    
    if settings.reload:
        reload_dirs = ["app"]  # Watch app/ directory including templates and static files
        reload_includes = ["*.py", "*.html", "*.css", "*.js"]
        logger.info("🔄 Hot reload enabled for Python, templates, and static files")
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        reload_dirs=reload_dirs,
        reload_includes=reload_includes,
        log_level=settings.log_level.lower()
    ) 