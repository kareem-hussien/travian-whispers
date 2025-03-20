"""
Travian settings routes for user dashboard.
This module defines the routes for Travian account management.
"""
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.activity import UserActivity

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/travian-settings', methods=['GET', 'POST'])
    @login_required
    def travian_settings():
        """Travian account settings route."""
        # Get user data
        user_model = User()
        user = user_model.get_user_by_id(session['user_id'])
        
        if not user:
            # Flash error message
            flash('User not found', 'danger')
            
            # Clear session and redirect to login
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Process form submission
        if request.method == 'POST':
            # Get form data
            travian_username = request.form.get('travian_username', '')
            travian_password = request.form.get('travian_password', '')
            travian_server = request.form.get('travian_server', '')
            travian_tribe = request.form.get('travian_tribe', '')
            
            # Check for changes in password field
            if travian_password == '********':
                # Password field was not changed, use existing password
                travian_password = user['travianCredentials']['password']
            
            # Update travian credentials
            update_data = {
                'travianCredentials': {
                    'username': travian_username,
                    'password': travian_password,
                    'server': travian_server,
                    'tribe': travian_tribe
                }
            }
            
            # Update user in database
            if user_model.update_user(session['user_id'], update_data):
                # Flash success message
                flash('Travian account settings updated successfully', 'success')
                logger.info(f"User '{user['username']}' updated Travian settings")
            else:
                # Flash error message
                flash('Failed to update Travian account settings', 'danger')
                logger.warning(f"Failed to update Travian settings for user '{user['username']}'")
        
        # Get user's last connection from activity logs
        activity_model = UserActivity()
        connection_logs = activity_model.get_activities_by_type(session['user_id'], 'Travian Login', limit=1)
        last_connection = connection_logs[0]['timestamp'] if connection_logs else 'Never'
        
        if isinstance(last_connection, datetime):
            last_connection = last_connection.strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare travian settings data
        travian_settings = {
            'travian_credentials': {
                'username': user['travianCredentials'].get('username', ''),
                'password': '********' if user['travianCredentials'].get('password', '') else '',
                'server': user['travianCredentials'].get('server', ''),
                'tribe': user['travianCredentials'].get('tribe', '')
            },
            'last_connection': last_connection
        }
        
        # Render travian settings template
        return render_template(
            'user/travian_settings.html', 
            user_profile=travian_settings,
            current_user=user, 
            title='Travian Settings'
        )