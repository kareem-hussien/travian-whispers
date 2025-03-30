"""
Travian settings routes for Travian Whispers web application.
"""
import logging
from flask import (
    render_template, request, redirect, 
    url_for, flash, session
)

from web.utils.decorators import login_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register travian settings routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/travian-settings', methods=['GET', 'POST'])(login_required(travian_settings))

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
    
    # Get last connection data from logs
    from database.models.activity_log import ActivityLog
    activity_model = ActivityLog()
    
    # Get latest connection activity
    connection_log = activity_model.get_latest_user_activity(
        user_id=session['user_id'],
        activity_type='travian-connection'
    )
    
    # Prepare travian settings data
    travian_settings = {
        'travian_credentials': {
            'username': user['travianCredentials'].get('username', ''),
            'password': '********' if user['travianCredentials'].get('password', '') else '',
            'server': user['travianCredentials'].get('server', ''),
            'tribe': user['travianCredentials'].get('tribe', '')
        },
        'last_connection': connection_log['timestamp'].strftime('%Y-%m-%d %H:%M') if connection_log and connection_log.get('timestamp') else 'Never'
    }
    
    # Render travian settings template
    return render_template(
        'user/travian_settings.html', 
        user_profile=travian_settings,
        current_user=user, 
        title='Travian Settings'
    )
