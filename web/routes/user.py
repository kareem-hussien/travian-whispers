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

# Import route modules
from web.routes.user_api import (
    dashboard, profile, travian_settings, villages, 
    auto_farm, troop_trainer, activity_logs, 
    subscription, support
)

# Register routes with the blueprint
dashboard.register_routes(user_bp)
profile.register_routes(user_bp)
travian_settings.register_routes(user_bp)
villages.register_routes(user_bp)
auto_farm.register_routes(user_bp)
troop_trainer.register_routes(user_bp)
activity_logs.register_routes(user_bp)
subscription.register_routes(user_bp)
support.register_routes(user_bp)