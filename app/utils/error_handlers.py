from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
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
        
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors gracefully"""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "The server encountered an internal error and was unable to complete your request"
        }), 500
        
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors gracefully"""
        logger.warning(f"Bad request: {str(error)}")
        return jsonify({
            "error": "Bad Request",
            "message": "The server could not understand the request due to invalid syntax"
        }), 400
