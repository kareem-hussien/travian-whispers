"""
User API routes for Travian Whispers web application.
This package contains routes for the user dashboard.
"""

def register_user_routes(user_bp):
    """
    Register all user API routes with the user blueprint.
    
    Args:
        user_bp: Flask Blueprint for user routes
    """
    # Import all modules to register their routes
    from . import dashboard
    from . import profile
    from . import travian_settings
    from . import villages
    from . import auto_farm
    from . import troop_trainer
    from . import activity_logs
    from . import subscription
    from . import support
    
    # Each module will attach its routes to the user_bp
    dashboard.register_routes(user_bp)
    profile.register_routes(user_bp)
    travian_settings.register_routes(user_bp)
    villages.register_routes(user_bp)
    auto_farm.register_routes(user_bp)
    troop_trainer.register_routes(user_bp)
    activity_logs.register_routes(user_bp)
    subscription.register_routes(user_bp)
    support.register_routes(user_bp)
