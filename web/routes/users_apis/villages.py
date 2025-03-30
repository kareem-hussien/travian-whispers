"""
Villages management routes for Travian Whispers web application.
"""
import logging
from flask import (
    render_template, flash, session, redirect, url_for
)

from web.utils.decorators import login_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register villages routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/villages')(login_required(villages))

@login_required
def villages():
    """Villages management route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Prepare villages data
    villages_data = user['villages']
    
    # Render villages template
    return render_template(
        'user/villages.html', 
        villages=villages_data,
        current_user=user, 
        title='Villages Management'
    )
