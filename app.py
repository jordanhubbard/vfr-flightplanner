from dotenv import load_dotenv
import os

# Load .env from the same directory as app.py
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Use the app factory pattern
from app import create_app
from app.config import DevelopmentConfig

app = create_app(DevelopmentConfig)

@app.after_request
def add_header(response):
    """Add headers for caching control."""
    if app.debug:
        # In debug mode, prevent caching
        response.headers['Cache-Control'] = 'no-store'
    else:
        # In production, cache static files
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=600'
    return response

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors gracefully"""
    if request.path == '/ws':
        logger.warning("WebSocket connection attempted but not supported")
        return jsonify({
            "error": "WebSocket connections are not supported",
            "message": "This endpoint only supports HTTP requests"
        }), 404
    return jsonify({
        "error": "Not Found",
        "message": f"The requested URL {request.path} was not found on the server"
    }), 404

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=port) 