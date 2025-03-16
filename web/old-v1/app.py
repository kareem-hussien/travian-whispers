"""
Flask application factory for Travian Whispers.
"""
import os
import logging
from flask import Flask

def create_app(test_config=None):
    """Create and configure the Flask application."""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Configure the app
    if test_config is None:
        app.config.from_pyfile('../config.py')
    else:
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize database
    from .utils.database import init_database
    init_database(app)
    
    # Register error handlers
    from .utils.errors import init_error_handlers
    init_error_handlers(app)
    
    # Register blueprints
    from .routes import register_blueprints
    register_blueprints(app)
    
    # Add context processor for user data
    from .utils.context_processors import inject_user
    app.context_processor(inject_user)
    
    return app