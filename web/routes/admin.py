"""
Admin routes for Travian Whispers web application.
This module defines the blueprint for admin panel routes.
"""
import logging
from flask import Blueprint

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import and register routes from admin_apis modules
from web.routes.admin_apis import register_admin_routes
register_admin_routes(admin_bp)
