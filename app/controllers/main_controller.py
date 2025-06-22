from flask import Blueprint, render_template, request
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main index page."""
    # Get coordinates from URL parameters, defaulting to None if not provided
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    return render_template('index.html',
                         api_key=os.getenv('OPENWEATHERMAP_API_KEY', ''),
                         initial_lat=lat,
                         initial_lon=lon)
