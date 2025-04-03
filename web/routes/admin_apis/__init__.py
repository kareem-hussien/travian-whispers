"""
Admin API routes for Travian Whispers web application.
This package contains routes for the admin panel APIs.
"""

def register_admin_routes(admin_bp):
    """
    Register all admin API routes with the admin blueprint.
    
    Args:
        admin_bp: Flask Blueprint for admin routes
    """
    # Import all modules to register their routes
    from . import dashboard
    from . import users
    from . import subscriptions
    from . import transactions
    from . import maintenance
    from . import settings
    from . import logs
    
    # Each module will attach its routes to the admin_bp
    dashboard.register_routes(admin_bp)
    users.register_routes(admin_bp)
    subscriptions.register_routes(admin_bp)
    transactions.register_routes(admin_bp)
    maintenance.register_routes(admin_bp)
    settings.register_routes(admin_bp)
    logs.register_routes(admin_bp)