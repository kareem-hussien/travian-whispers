"""
Activity Logs routes for user dashboard.
This module defines the routes for activity logs.
"""
import logging
from flask import render_template, request, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.activity import UserActivity

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/activity-logs')
    @login_required
    def activity_logs():
        """Activity logs route."""
        # Get user data
        user_model = User()
        user = user_model.get_user_by_id(session['user_id'])
        
        if not user:
            # Flash error message
            flash('User not found', 'danger')
            
            # Clear session and redirect to login
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get activity logs from database
        activity_model = UserActivity()
        
        # Set up pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        skip = (page - 1) * per_page
        
        # Get activity logs with pagination
        activities_cursor = activity_model.get_user_activities(
            user_id=session['user_id'],
            skip=skip,
            limit=per_page
        )
        
        # Convert cursor to list
        activity_logs = list(activities_cursor)
        
        # Get total count for pagination
        total_logs = activity_model.count_user_activities(session['user_id'])
        total_pages = (total_logs + per_page - 1) // per_page
        
        # Render activity logs template
        return render_template(
            'user/activity_logs.html', 
            logs=activity_logs,
            current_page=page,
            total_pages=total_pages,
            current_user=user, 
            title='Activity Logs'
        )