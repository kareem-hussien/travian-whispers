"""
Error handlers for Travian Whispers web application.
This module registers error handlers for the Flask application.
"""
import logging
from flask import render_template, request, jsonify

# Initialize logger
logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Base class for API errors."""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert error to dictionary for JSON response."""
        result = {}
        result['success'] = False
        result['message'] = self.message
        if self.payload:
            result['data'] = self.payload
        return result


def handle_api_error(error):
    """
    Handle ApiError exceptions for API routes.
    
    Args:
        error: ApiError instance
        
    Returns:
        JSON response with error details
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_not_found_error(error):
    """
    Handle 404 Not Found errors.
    
    Args:
        error: NotFound exception
        
    Returns:
        JSON response or error template
    """
    # Check if this is an API request
    if request.path.startswith('/api/'):
        response = jsonify({
            'success': False,
            'message': 'The requested resource was not found'
        })
        response.status_code = 404
        return response
    
    # For regular routes, render a 404 template
    return render_template('errors/404.html'), 404


def handle_method_not_allowed(error):
    """
    Handle 405 Method Not Allowed errors.
    
    Args:
        error: MethodNotAllowed exception
        
    Returns:
        JSON response or error template
    """
    # Check if this is an API request
    if request.path.startswith('/api/'):
        response = jsonify({
            'success': False,
            'message': 'The method is not allowed for the requested URL'
        })
        response.status_code = 405
        return response
    
    # For regular routes, render a general error template
    return render_template('errors/error.html', error_code=405, error_name='Method Not Allowed'), 405


def handle_internal_server_error(error):
    """
    Handle 500 Internal Server Error errors.
    
    Args:
        error: InternalServerError exception
        
    Returns:
        JSON response or error template
    """
    # Log the error
    logger.error(f"Internal server error: {str(error)}")
    
    # Check if this is an API request
    if request.path.startswith('/api/'):
        response = jsonify({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        })
        response.status_code = 500
        return response
    
    # For regular routes, render a 500 template
    return render_template('errors/500.html'), 500


def register_error_handlers(app):
    """
    Register error handlers for Flask application.
    
    Args:
        app: Flask application instance
    """
    app.register_error_handler(ApiError, handle_api_error)
    app.register_error_handler(404, handle_not_found_error)
    app.register_error_handler(405, handle_method_not_allowed)
    app.register_error_handler(500, handle_internal_server_error)
    
    logger.info("Error handlers registered")