"""
Help and support routes for Travian Whispers web application.
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
    """Register support routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/support')(login_required(support))

@login_required
def support():
    """Help and support route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Render support template
    return render_template(
        'user/support.html', 
        current_user=user, 
        title='Help & Support'
    )
