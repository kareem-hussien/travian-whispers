"""
Flask application factory for Travian Whispers.
This module defines the application factory function that creates
and configures the Flask application.
"""
import os
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from web.extensions import register_extensions
from web.routes import register_blueprints
from web.utils.error_handlers import register_error_handlers
from web.utils.context_processors import register_context_processors
from web.utils.json_encoder import TravianJSONEncoder

def create_app(config_object=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_object: Configuration object or path
        
    Returns:
        Flask application instance
    """
    # Initialize Flask app
    app = Flask(__name__, 
                instance_relative_config=True,
                template_folder='templates',
                static_folder='static')
    
    # Configure the app
    configure_app(app, config_object)
    
    # Fix for running behind proxy
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Set custom JSON encoder
    app.json_encoder = TravianJSONEncoder
    
    # Register extensions
    register_extensions(app)
    
    # Enable CORS
    CORS(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    return app

def configure_app(app, config_object=None):
    """
    Configure the Flask application with appropriate settings.
    
    Args:
        app: Flask application instance
        config_object: Configuration object or path
    """
    # Load default configuration
    app.config.from_object('web.config.DevelopmentConfig')
    
    # Load configuration from file specified by environment variable
    if os.environ.get('TRAVIAN_WHISPERS_CONFIG'):
        app.config.from_envvar('TRAVIAN_WHISPERS_CONFIG')
    
    # Load configuration from object if provided
    if config_object:
        if isinstance(config_object, str):
            app.config.from_pyfile(config_object)
        else:
            app.config.from_object(config_object)
            
    # Set server name if specified in environment
    if os.environ.get('SERVER_NAME'):
        app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')
