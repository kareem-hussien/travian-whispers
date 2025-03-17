"""
Context processors for Travian Whispers web application.
This module provides context processors for Jinja2 templates.
"""
import logging
from flask import session
from datetime import datetime

from web.utils.helpers import (
    format_datetime, format_currency, 
    get_subscription_status_badge, get_transaction_status_badge
)

# Initialize logger
logger = logging.getLogger(__name__)


def inject_user():
    """Inject user data into templates."""
    # Initialize default values
    user_data = {
        'is_authenticated': False,
        'is_admin': False,
        'username': None,
        'email': None
    }
    
    # Check if user is authenticated
    if 'user_id' in session:
        user_data['is_authenticated'] = True
        user_data['username'] = session.get('username')
        user_data['email'] = session.get('email')
        user_data['is_admin'] = session.get('role') == 'admin'
    
    # Return both user_data and current_user to maintain compatibility
    return {
        'user_data': user_data,
        'current_user': user_data  # This ensures current_user is always defined
    }


def inject_helpers():
    """Inject helper functions into templates."""
    return {
        'format_datetime': format_datetime,
        'format_currency': format_currency,
        'get_subscription_status_badge': get_subscription_status_badge,
        'get_transaction_status_badge': get_transaction_status_badge,
        'current_year': datetime.now().year
    }


def register_context_processors(app):
    """
    Register context processors for Flask application.
    
    Args:
        app: Flask application instance
    """
    app.context_processor(inject_user)
    app.context_processor(inject_helpers)
    
    logger.info("Context processors registered")