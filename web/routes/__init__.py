"""
Blueprint registration for Travian Whispers web application.
This module registers all blueprints for the Flask application.
"""
import logging
from flask import Flask

def register_blueprints(app: Flask):
    """
    Register all application blueprints.
    
    Args:
        app: Flask application instance
    """
    logger = logging.getLogger(__name__)
    
    # Import blueprints
    from web.routes.auth import auth_bp
    from web.routes.user import user_bp
    from web.routes.admin import admin_bp
    from web.routes.api import api_bp
    from web.routes.public import public_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(public_bp)
    
    # Register IP routes if they exist
    try:
        from web.routes.ip_routes import ip_bp
        app.register_blueprint(ip_bp)
        logger.info("IP routes registered")
    except ImportError:
        logger.debug("IP routes not available")
    
    # Register villages API routes
    try:
        from web.routes.villages_api import register_routes as register_villages_routes
        register_villages_routes(app)
        logger.info("Villages API routes registered")
    except ImportError:
        logger.debug("Villages API routes not available")
    
    # Register Travian API routes if they exist
    try:
        from web.routes.travian_api import register_routes as register_travian_api_routes
        register_travian_api_routes(app)
        logger.info("Travian API routes registered")
    except ImportError:
        logger.debug("Travian API routes not available")
    
    logger.info("All blueprints registered")