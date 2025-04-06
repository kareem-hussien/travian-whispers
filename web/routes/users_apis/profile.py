"""
User profile routes for Travian Whispers web application.
"""
import logging
from datetime import timezone
from datetime import datetime
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app
)

from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.activity_log import ActivityLog
from auth.password_reset import change_password

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register profile routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/profile', methods=['GET', 'POST'])(login_required(profile))

@login_required
def profile():
    """User profile route."""
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
        form_type = request.form.get('form_type', '')
        
        if form_type == 'profile':
            # Update profile information
            notification_email = 'notification_email' in request.form
            auto_renew = 'auto_renew' in request.form
            
            # Update settings (email is not included as it cannot be changed)
            update_data = {
                'settings': {
                    'notification': notification_email,
                    'autoRenew': auto_renew,
                    # Preserve existing settings
                    'autoFarm': user['settings'].get('autoFarm', False),
                    'trainer': user['settings'].get('trainer', False),
                }
            }
            
            # Update user in database
            if user_model.update_user(session['user_id'], update_data):
                # Log the activity
                activity_model = ActivityLog()
                activity_model.log_activity(
                    user_id=session['user_id'],
                    activity_type='profile-update',
                    details='Profile information updated',
                    status='success'
                )
                
                # Flash success message
                flash('Profile updated successfully', 'success')
                logger.info(f"User '{user['username']}' updated profile")
            else:
                # Flash error message
                flash('Failed to update profile', 'danger')
                logger.warning(f"Failed to update profile for user '{user['username']}'")
                
        elif form_type == 'password':
            # Change password
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Update password
            success, message = change_password(
                session['user_id'],
                current_password,
                new_password,
                confirm_password
            )
            
            # Flash appropriate message
            if success:
                # Log the activity
                activity_model = ActivityLog()
                activity_model.log_activity(
                    user_id=session['user_id'],
                    activity_type='password-change',
                    details='Password changed successfully',
                    status='success'
                )
                
                flash(message, 'success')
                logger.info(f"User '{user['username']}' changed password")
            else:
                flash(message, 'danger')
                logger.warning(f"Failed to change password for user '{user['username']}': {message}")
    
    # Get current subscription plan if available
    plan_model = SubscriptionPlan()
    current_plan = None
    
    if user['subscription']['planId']:
        plan = plan_model.get_plan_by_id(user['subscription']['planId'])
        if plan:
            current_plan = plan['name']
    
    # Get user activity statistics
    activity_model = ActivityLog()
    
    # Count activities for the user
    activity_count = activity_model.count_user_activities(user_id=session['user_id'])
    
    # Get recent login activity
    login_activity = activity_model.get_latest_user_activity(
        user_id=session['user_id'],
        activity_type='login'
    )
    
    last_login_date = None
    if login_activity and 'timestamp' in login_activity:
        last_login_date = login_activity['timestamp']
    
    # Get account age in days
    utcnow_aware = datetime.utcnow().replace(tzinfo=timezone.utc)
    account_age_days = (utcnow_aware - user['createdAt']).days
    
    # Prepare user profile data
    user_profile = {
        'username': user['username'],
        'email': user['email'],
        'settings': {
            'notification_email': user['settings'].get('notification', True),
            'auto_renew': user['settings'].get('autoRenew', False)
        },
        'subscription': {
            'status': user['subscription']['status'],
            'plan': current_plan or 'None',
            'start_date': user['subscription'].get('startDate'),
            'end_date': user['subscription'].get('endDate')
        },
        'stats': {
            'account_age': account_age_days,
            'activities': activity_count,
            'last_login': last_login_date or user.get('lastLoginAt', 'Never'),
            'villages_count': len(user['villages'])
        }
    }
    
    # Render profile template
    return render_template(
        'user/profile.html', 
        user_profile=user_profile,
        current_user=user, 
        title='Profile Settings'
    )