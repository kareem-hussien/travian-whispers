"""
Utils package for Travian Whispers web application.
This module initializes the utils package and imports common utilities for ease of access.
"""
import logging

# Import common utilities for easy access
from web.utils.decorators import login_required, admin_required, redirect_if_authenticated, api_error_handler
from web.utils.helpers import (
    get_ip_address, get_current_user, render_error_page,
    format_datetime, format_currency,
    get_subscription_status_badge, get_transaction_status_badge
)
from web.utils.json_encoder import TravianJSONEncoder
from web.utils.error_handlers import ApiError, register_error_handlers
from web.utils.context_processors import register_context_processors

# Initialize logger
logger = logging.getLogger(__name__)

# Package version
__version__ = '1.0.0'

# Export common utilities
__all__ = [
    'login_required',
    'admin_required',
    'redirect_if_authenticated',
    'api_error_handler',
    'get_ip_address',
    'get_current_user',
    'render_error_page',
    'format_datetime',
    'format_currency',
    'get_subscription_status_badge',
    'get_transaction_status_badge',
    'TravianJSONEncoder',
    'ApiError',
    'register_error_handlers',
    'register_context_processors'
]