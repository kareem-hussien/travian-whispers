"""
User routes for Travian Whispers web application.
This module defines the blueprint for user dashboard routes.
"""
import logging
from flask import Blueprint

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
user_bp = Blueprint('user', __name__, url_prefix='/dashboard')

# Import and register routes from users_apis modules
from web.routes.users_apis import register_user_routes
register_user_routes(user_bp)
