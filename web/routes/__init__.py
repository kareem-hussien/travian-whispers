"""
Blueprint registration for Travian Whispers web application.
This module registers all blueprints for the Flask application.
"""
import logging

def register_blueprints(app):
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
    
    logger.info("All blueprints registered")
