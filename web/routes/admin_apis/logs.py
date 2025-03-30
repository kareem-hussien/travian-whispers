"""
Admin logs routes for Travian Whispers web application.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app
)

from web.utils.decorators import admin_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register logs routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/logs')(admin_required(logs))

def logs():
    """System logs page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Mock log data
    logs = [
        {
            'id': 1,
            'timestamp': datetime.now() - timedelta(hours=1),
            'level': 'INFO',
            'user': 'admin',
            'action': 'System backup created',
            'ip_address': '192.168.1.1',
            'details': 'Full backup completed successfully'
        },
        {
            'id': 2,
            'timestamp': datetime.now() - timedelta(hours=2),
            'level': 'WARNING',
            'user': 'system',
            'action': 'High memory usage detected',
            'ip_address': '127.0.0.1',
            'details': 'Memory usage reached 85%'
        },
        {
            'id': 3,
            'timestamp': datetime.now() - timedelta(hours=3),
            'level': 'ERROR',
            'user': 'john_doe',
            'action': 'Failed login attempt',
            'ip_address': '192.168.1.2',
            'details': 'Multiple failed login attempts detected'
        },
        {
            'id': 4,
            'timestamp': datetime.now() - timedelta(hours=5),
            'level': 'INFO',
            'user': 'jane_smith',
            'action': 'Subscription upgraded',
            'ip_address': '192.168.1.3',
            'details': 'Upgraded from Basic to Premium plan'
        },
        {
            'id': 5,
            'timestamp': datetime.now() - timedelta(hours=8),
            'level': 'INFO',
            'user': 'admin',
            'action': 'User account created',
            'ip_address': '192.168.1.1',
            'details': 'Created new user: new_user'
        }
    ]
    
    # Filter logs based on query parameters
    log_level = request.args.get('level')
    user_filter = request.args.get('user')
    
    if log_level:
        logs = [log for log in logs if log['level'].lower() == log_level.lower()]
    
    if user_filter:
        logs = [log for log in logs if user_filter.lower() in log['user'].lower()]
    
    # Count logs by level
    info_count = sum(1 for log in logs if log['level'] == 'INFO')
    warning_count = sum(1 for log in logs if log['level'] == 'WARNING')
    error_count = sum(1 for log in logs if log['level'] == 'ERROR')
    
    # Create log stats dictionary
    log_stats = {
        'total': len(logs),
        'info': info_count,
        'warning': warning_count,
        'error': error_count
    }
    
    # Render logs template
    return render_template(
        'admin/logs.html',
        logs=logs,
        log_stats=log_stats,
        current_user=current_user,
        title='System Logs'
    )
