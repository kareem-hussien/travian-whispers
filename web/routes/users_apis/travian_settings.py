"""
Enhanced Travian settings module with automatic village extraction.
"""
import logging
import time
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, jsonify
)

from web.utils.decorators import login_required
from database.models.user import User
from database.models.activity_log import ActivityLog

# Import needed for connection testing
try:
    from travian_api.connector import test_connection
except ImportError:
    # Define a fallback function if the module is not available
    def test_connection(username, password, server_url, timeout=30):
        logger.warning("travian_api.connector module not available, using fallback")
        return {
            'success': False,
            'message': "Connection test not available - module not installed"
        }
        
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
        
        # Validate inputs
        error = False
        if not travian_username:
            flash('Travian username is required', 'danger')
            error = True
            
        # Check for changes in password field
        if travian_password == '********':
            # Password field was not changed, use existing password
            travian_password = user['travianCredentials'].get('password', '')
        elif not travian_password:
            flash('Travian password is required', 'danger')
            error = True
            
        if error:
            # If there were validation errors, don't update and re-render the form
            # with the current values
            travian_settings = {
                'travian_credentials': {
                    'username': travian_username,
                    'password': '********' if user['travianCredentials'].get('password', '') else '',
                    'server': travian_server,
                    'tribe': travian_tribe
                },
                'last_connection': 'Never',  # Default value
                'connection_verified': False,
                'show_verify_button': True
            }
            
            # Try to get connection log information
            try:
                from database.models.activity_log import ActivityLog
                activity_model = ActivityLog()
                connection_log = activity_model.get_latest_user_activity(
                    user_id=session['user_id'],
                    activity_type='travian-connection'
                )
                
                if connection_log and connection_log.get('timestamp'):
                    travian_settings['last_connection'] = connection_log['timestamp'].strftime('%Y-%m-%d %H:%M')
                    travian_settings['connection_verified'] = connection_log.get('status') == 'success'
            except Exception as e:
                logger.error(f"Error getting connection log: {e}")
            
            return render_template(
                'user/travian_settings.html', 
                user_profile=travian_settings,
                current_user=user, 
                title='Travian Settings'
            )
        
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
            
            # Attempt to verify connection with Travian servers and extract villages
            connection_verified = False
            villages_extracted = False
            villages_count = 0
            try:
                # Test the connection
                from travian_api.connector import test_connection
                connection_result = test_connection(
                    travian_username, 
                    travian_password, 
                    travian_server
                )
                connection_verified = connection_result['success']
                
                if connection_verified:
                    flash('Travian account successfully connected and verified!', 'success')
                    logger.info(f"Travian connection verified for user '{user['username']}'")
                    
                    # Now automatically extract villages
                    try:
                        # Notify user that we're extracting villages
                        flash('Extracting villages from your Travian account...', 'info')
                        
                        # Import the extract_villages function
                        try:
                            from web.routes.users_apis.villages import extract_villages_internal
                            
                            # Extract villages
                            extraction_result = extract_villages_internal(session['user_id'])
                            
                            if extraction_result.get('success'):
                                villages_extracted = True
                                villages_count = len(extraction_result.get('data', []))
                                flash(f'Successfully extracted {villages_count} villages from your Travian account!', 'success')
                                logger.info(f"Villages extracted for user '{user['username']}': {villages_count}")
                            else:
                                flash(f"Villages could not be extracted: {extraction_result.get('message', 'Unknown error')}", 'warning')
                                logger.warning(f"Village extraction failed for user '{user['username']}': {extraction_result.get('message', 'Unknown error')}")
                        except ImportError:
                            logger.warning("extract_villages_internal function not available")
                            flash('Villages could not be extracted automatically. Please use the Extract Villages button on the Villages page.', 'warning')
                    except Exception as e:
                        logger.error(f"Error during village extraction: {e}")
                        flash('Connection verified, but village extraction failed. Please try manually extracting villages.', 'warning')
                else:
                    flash(f"Settings saved but connection could not be verified: {connection_result.get('message', 'Unknown error')}", 'warning')
                    logger.warning(f"Travian connection failed for user '{user['username']}': {connection_result.get('message', 'Unknown error')}")
            except ImportError:
                logger.warning("Travian API connector module not available, connection verification skipped")
                flash('Settings saved. To verify your connection, please visit the Villages page and click "Extract Villages".', 'info')
            except Exception as e:
                logger.error(f"Error verifying Travian connection: {e}")
                flash('Settings saved but there was an error verifying the connection', 'warning')
            
            # Log the activity
            try:
                from database.models.activity_log import ActivityLog
                activity_model = ActivityLog()
                
                # Log different activity based on verification result
                if connection_verified:
                    activity_model.log_activity(
                        user_id=session['user_id'],
                        activity_type='travian-connection',
                        details='Successfully connected to Travian account',
                        status='success',
                        data={
                            'villages_extracted': villages_extracted,
                            'villages_count': villages_count
                        }
                    )
                else:
                    activity_model.log_activity(
                        user_id=session['user_id'],
                        activity_type='travian-settings-update',
                        details='Updated Travian account settings',
                        status='success'
                    )
            except Exception as e:
                logger.error(f"Error logging activity: {e}")
        else:
            # Flash error message
            flash('Failed to update Travian account settings', 'danger')
            logger.warning(f"Failed to update Travian settings for user '{user['username']}'")
    
    # Get last connection data from logs
    connection_log = None
    travian_settings = {
        'travian_credentials': {
            'username': user['travianCredentials'].get('username', ''),
            'password': '********' if user['travianCredentials'].get('password', '') else '',
            'server': user['travianCredentials'].get('server', ''),
            'tribe': user['travianCredentials'].get('tribe', '')
        },
        'last_connection': 'Never',  # Default value
        'connection_verified': False,
        'show_verify_button': True,
        'villages_count': len(user.get('villages', []))
    }
    
    try:
        from database.models.activity_log import ActivityLog
        activity_model = ActivityLog()
        
        # Get latest connection activity
        connection_log = activity_model.get_latest_user_activity(
            user_id=session['user_id'],
            activity_type='travian-connection'
        )
        
        # Update last connection if available
        if connection_log and connection_log.get('timestamp'):
            travian_settings['last_connection'] = connection_log['timestamp'].strftime('%Y-%m-%d %H:%M')
            travian_settings['connection_verified'] = connection_log.get('status') == 'success'
            travian_settings['show_verify_button'] = False
    except Exception as e:
        logger.error(f"Error getting connection log: {e}")
    
    # Render travian settings template
    return render_template(
        'user/travian_settings.html', 
        user_profile=travian_settings,
        current_user=user, 
        title='Travian Settings'
    )
