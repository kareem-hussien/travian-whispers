"""
Flask extensions initialization for Travian Whispers.
This module initializes all the Flask extensions used in the application.
"""
import logging
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
session = Session()
csrf = CSRFProtect()

def register_extensions(app):
    """
    Register Flask extensions with the application.
    
    Args:
        app: Flask application instance
    """
    # Configure session
    session.init_app(app)
    
    # Enable CSRF protection
    csrf.init_app(app)
    
    # Configure logging
    configure_logging(app)
    
    # Initialize database connection (via MongoDB class)
    init_database(app)
    
    logger = logging.getLogger(__name__)
    logger.info("Flask extensions initialized")

def configure_logging(app):
    """
    Configure application logging.
    
    Args:
        app: Flask application instance
    """
    if not app.debug and not app.testing:
        # Set up production logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        
        # Set up file logging if configured
        if app.config.get('LOG_FILE'):
            file_handler = logging.FileHandler(app.config['LOG_FILE'])
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
    app.logger.info('Logging configured')

def init_database(app):
    """
    Initialize database connection.
    
    Args:
        app: Flask application instance
    """
    # Import database connection here to avoid circular imports
    from database.mongodb import MongoDB
    
    db = MongoDB()
    
    # Use config values from Flask app
    uri = app.config.get('MONGODB_URI') 
    db_name = app.config.get('MONGODB_DB_NAME')
    
    # Connect to database
    if not db.connect(connection_string=uri, db_name=db_name):
        app.logger.error("Failed to connect to MongoDB")
    else:
        app.logger.info("Connected to MongoDB successfully")
        
        # Create indexes if not in testing mode
        if not app.testing:
            db.create_indexes()
            
    # Store database instance in app context
    app.db = db
