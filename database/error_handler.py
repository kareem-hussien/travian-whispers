"""
MongoDB error handling module for Travian Whispers.
"""
import logging
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError, 
    NetworkTimeout,
    OperationFailure,
    DuplicateKeyError
)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database.error_handler')

class DatabaseError(Exception):
    """Base class for all database-related errors."""
    def __init__(self, message, original_error=None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class ConnectionError(DatabaseError):
    """Error raised when the database connection fails."""
    pass

class QueryError(DatabaseError):
    """Error raised when a database query fails."""
    pass

class ValidationError(DatabaseError):
    """Error raised when data validation fails."""
    pass

class DuplicateError(DatabaseError):
    """Error raised when attempting to insert a duplicate record."""
    pass

def sanitize_sensitive_data(message):
    """Sanitize potentially sensitive data from log messages."""
    # List of patterns to replace
    patterns = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', 'password=***'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\']+)["\']?', 'token=***'),
        # Add more patterns as needed
    ]
    
    sanitized = message
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    return sanitized

def log_database_activity(activity_type):
    """Decorator to log database activities."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Database {activity_type} started: {func.__name__}")
            result = func(*args, **kwargs)
            # Sanitize any log messages
            sanitized_result = sanitize_sensitive_data(str(result)) if result else None
            logger.info(f"Database {activity_type} completed: {func.__name__}")
            return result
        return wrapper
    return decorator

def handle_connection_error(func):
    """
    Decorator to handle database connection errors.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ConnectionFailure, ServerSelectionTimeoutError, NetworkTimeout) as e:
            error_msg = f"Database connection error: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg, e)
    return wrapper

def handle_operation_error(func):
    """
    Decorator to handle database operation errors.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationFailure as e:
            error_msg = f"Database operation error: {str(e)}"
            logger.error(error_msg)
            raise QueryError(error_msg, e)
        except DuplicateKeyError as e:
            error_msg = f"Duplicate key error: {str(e)}"
            logger.error(error_msg)
            raise DuplicateError(error_msg, e)
        except Exception as e:
            error_msg = f"Unexpected database error: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, e)
    return wrapper

def log_database_activity(activity_type):
    """
    Decorator to log database activities.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Database {activity_type} started: {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"Database {activity_type} completed: {func.__name__}")
            return result
        return wrapper
    return decorator