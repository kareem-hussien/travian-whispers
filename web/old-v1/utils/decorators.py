# web/utils/decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash, request, current_app

def login_required(view_func):
    """Decorator to require login for views."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        return view_func(*args, **kwargs)
    return wrapped_view

def admin_required(view_func):
    """Decorator to require admin role for views."""
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('user.dashboard'))
        
        return view_func(*args, **kwargs)
    return wrapped_view