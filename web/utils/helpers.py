"""
Helper functions for Travian Whispers web application.
This module provides utility functions for the application.
"""
import logging
import json
from bson import ObjectId
from flask import request, session, render_template, current_app
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)


def json_serialize(obj):
    """
    JSON serialization helper that handles ObjectId and datetime objects.
    Replacement for the custom JSONEncoder class.
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Let the default JSON serializer handle it (may raise a TypeError)
    return obj


def get_ip_address():
    """Get the client's IP address."""
    if request.headers.getlist("X-Forwarded-For"):
        # For proxied requests
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0]
    else:
        ip = request.remote_addr
    return ip


def get_current_user():
    """Get the current authenticated user."""
    from database.models.user import User
    
    if 'user_id' not in session:
        return None
    
    user_model = User()
    return user_model.get_user_by_id(session['user_id'])


def render_error_page(error_code, message=None):
    """Render an error page."""
    if error_code == 404:
        return render_template('errors/404.html', message=message), 404
    elif error_code == 500:
        return render_template('errors/500.html', message=message), 500
    else:
        return render_template('errors/error.html', error_code=error_code, message=message), error_code


def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object as a string."""
    if dt is None:
        return 'N/A'
    return dt.strftime(format_str)


def format_currency(amount, currency='$'):
    """Format a currency amount."""
    if amount is None:
        return 'N/A'
    return f"{currency}{amount:.2f}"


def get_subscription_status_badge(status):
    """Get a Bootstrap badge class for a subscription status."""
    if status == 'active':
        return 'bg-success'
    elif status == 'cancelled':
        return 'bg-warning'
    elif status == 'expired':
        return 'bg-danger'
    else:
        return 'bg-secondary'


def get_transaction_status_badge(status):
    """Get a Bootstrap badge class for a transaction status."""
    if status == 'completed':
        return 'bg-success'
    elif status == 'pending':
        return 'bg-warning'
    elif status == 'failed':
        return 'bg-danger'
    elif status == 'refunded':
        return 'bg-info'
    else:
        return 'bg-secondary'
