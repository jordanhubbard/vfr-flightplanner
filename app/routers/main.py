"""
Main Router.

Provides endpoints for the web interface and static file serving.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter()

# Mount static files and templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Serve the main web interface.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Main web interface
    """
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving main page: {e}")
        return HTMLResponse(
            content="<h1>VFR Flight Planner</h1><p>Service temporarily unavailable</p>",
            status_code=500
        )


@router.get("/favicon.ico")
async def favicon():
    """
    Serve favicon.
    
    Returns:
        FileResponse: Favicon file
    """
    return FileResponse("app/static/favicon.ico")


# Additional web interface endpoints can be added here
# Examples:
# - Flight plan viewer
# - Weather maps
# - Airport information pages
# - Help documentation 