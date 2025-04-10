"""
Villages API routes for Travian Whispers web application.
"""
from flask import Flask

def register_routes(app: Flask):
    """
    Register villages API routes with the application.
    
    Args:
        app: Flask application instance
    """
    from web.routes.villages_api.routes import villages_api_bp
    app.register_blueprint(villages_api_bp)