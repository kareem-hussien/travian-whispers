"""
Error handler for the Travian Whispers web application.
"""
import logging
import traceback
from functools import wraps
from flask import jsonify, render_template, request, current_app

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web.error_handler')

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

def handle_general_exception(error):
    """
    Handle general exceptions for API routes.
    
    Args:
        error: Exception instance
        
    Returns:
        JSON response with error details or error template
    """
    # Log the error
    logger.error(f"Unhandled exception: {str(error)}")
    logger.error(traceback.format_exc())
    
    # Check if this is an API request
    if request.path.startswith('/api/'):
        response = jsonify({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.'
        })
        response.status_code = 500
        return response
    
    # For regular routes, render an error template
    return render_template('errors/500.html', error=str(error)), 500

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
            'message': 'The requested resource was not found.'
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
            'message': 'The method is not allowed for the requested URL.'
        })
        response.status_code = 405
        return response
    
    # For regular routes, render a general error template
    return render_template('errors/405.html'), 405

def api_error_handler(func):
    """
    Decorator for API routes to handle exceptions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiError as e:
            return handle_api_error(e)
        except Exception as e:
            logger.error(f"Unhandled exception in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500
    return wrapper

def init_error_handlers(app):
    """
    Initialize error handlers for Flask application.
    
    Args:
        app: Flask application instance
    """
    app.register_error_handler(ApiError, handle_api_error)
    app.register_error_handler(404, handle_not_found_error)
    app.register_error_handler(405, handle_method_not_allowed)
    app.register_error_handler(Exception, handle_general_exception)
    
    logger.info("Error handlers initialized")
