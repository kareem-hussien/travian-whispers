"""
Profile routes for user dashboard.
This module defines the routes for user profile management.
"""
import logging
from flask import render_template, request, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/profile', methods=['GET', 'POST'])
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
                email = request.form.get('email', '')
                notification_email = 'notification_email' in request.form
                auto_renew = 'auto_renew' in request.form
                
                # Update settings
                update_data = {
                    'email': email,
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
                    # Update session data
                    session['email'] = email
                    
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
                from auth.password_reset import change_password
                success, message = change_password(
                    session['user_id'],
                    current_password,
                    new_password,
                    confirm_password
                )
                
                # Flash appropriate message
                if success:
                    flash(message, 'success')
                    logger.info(f"User '{user['username']}' changed password")
                else:
                    flash(message, 'danger')
                    logger.warning(f"Failed to change password for user '{user['username']}': {message}")
        
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
                'start_date': user['subscription'].get('startDate', 'N/A'),
                'end_date': user['subscription'].get('endDate', 'N/A')
            }
        }
        
        # Render profile template
        return render_template(
            'user/profile.html', 
            user_profile=user_profile,
            current_user=user, 
            title='Profile Settings'
        )