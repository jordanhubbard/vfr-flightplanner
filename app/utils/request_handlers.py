from flask import request

def register_after_request(app):
    """
    Register after_request handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
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
