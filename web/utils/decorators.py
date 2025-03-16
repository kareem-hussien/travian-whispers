"""
Custom decorators for Travian Whispers web application.
This module provides decorators for routes.
"""
import logging
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

# Initialize logger
logger = logging.getLogger(__name__)


def login_required(view_func):
    """Decorator to require login for views."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'message': 'Authentication required'
                }), 401
            else:
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.path))
        return view_func(*args, **kwargs)
    return wrapped_view


def admin_required(view_func):
    """Decorator to require admin role for views."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'message': 'Authentication required'
                }), 401
            else:
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.path))
        
        if session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'message': 'Admin access required'
                }), 403
            else:
                flash('Admin access required', 'danger')
                return redirect(url_for('user.dashboard'))
        
        return view_func(*args, **kwargs)
    return wrapped_view


def redirect_if_authenticated(view_func):
    """Decorator to redirect authenticated users."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' in session:
            # Redirect to appropriate dashboard based on role
            if session.get('role') == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        return view_func(*args, **kwargs)
    return wrapped_view


def api_error_handler(view_func):
    """
    Decorator for API routes to handle exceptions.
    
    Args:
        view_func: Function to decorate
        
    Returns:
        Wrapped function
    """
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unhandled exception in {view_func.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again later.'
            }), 500
    return wrapped_view