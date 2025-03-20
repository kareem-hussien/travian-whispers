"""
Villages routes for user dashboard.
This module defines the routes for village management.
"""
import logging
from flask import render_template, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.village import Village

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/villages')
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
        
        # Get villages from database
        village_model = Village()
        villages_data = village_model.get_user_villages(session['user_id'])
        
        # Render villages template
        return render_template(
            'user/villages.html', 
            villages=villages_data,
            current_user=user, 
            title='Villages Management'
        )