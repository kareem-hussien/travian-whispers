"""
Flask application factory for Travian Whispers.
This module defines the application factory function that creates
and configures the Flask application.
"""
import os
import json
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from bson import ObjectId
from datetime import datetime
from web.routes.travian_api import register_routes as register_travian_api_routes
from web.extensions import register_extensions
from web.routes import register_blueprints
from web.utils.error_handlers import register_error_handlers
from web.utils.context_processors import register_context_processors

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
    
    # Configure JSON serialization
    configure_json_serialization(app)
    
    # Register extensions
    register_extensions(app)
    
    # Register Travian API routes
    register_travian_api_routes(app)
    
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

def configure_json_serialization(app):
    """
    Configure JSON serialization for the Flask application.
    Uses a custom implementation to override Flask's default JSON serialization.
    
    Args:
        app: Flask application instance
    """
    # Create custom JSON encoder function
    def custom_json_encoder(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat() if obj else None
        raise TypeError(f"Type {type(obj)} not serializable")
    
    # Override Flask's jsonify to handle MongoDB ObjectId and datetime
    original_jsonify = jsonify
    
    def custom_jsonify(*args, **kwargs):
        if args and kwargs:
            raise TypeError('jsonify() behavior undefined when passed both args and kwargs')
        if len(args) == 1:
            data = args[0]
        else:
            data = args or kwargs
            
        # First convert to JSON string using the custom encoder
        dumped = json.dumps(data, default=custom_json_encoder)
        # Then parse it back to ensure it's fully serializable
        parsed = json.loads(dumped)
        # Now use Flask's original jsonify with the serialized data
        return original_jsonify(parsed)
    
    # Replace Flask's jsonify in the current module
    import flask
    flask.jsonify = custom_jsonify
    
    # Configure Flask JSON settings
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    app.config['JSON_SORT_KEYS'] = False
