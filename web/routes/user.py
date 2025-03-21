"""
User routes for Travian Whispers web application.
This module defines the blueprint for user dashboard routes.
"""
import logging
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
user_bp = Blueprint('user', __name__, url_prefix='/dashboard')


@user_bp.route('/')
@login_required
def dashboard():
    """User dashboard route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get subscription plan
    plan_model = SubscriptionPlan()
    plan = None
    if user['subscription']['planId']:
        plan = plan_model.get_plan_by_id(user['subscription']['planId'])
    
    # Prepare data for dashboard
    dashboard_data = {
        'username': user['username'],
        'email': user['email'],
        'subscription': {
            'status': user['subscription']['status'],
            'plan': plan['name'] if plan else 'None',
            'start_date': user['subscription']['startDate'],
            'end_date': user['subscription']['endDate'],
        },
        'villages': user['villages'],
        'auto_farm': {
            'status': 'active' if user['settings']['autoFarm'] else 'stopped',
            'last_run': 'Never', # This would be retrieved from activity logs
            'next_run': 'N/A',  # This would be calculated based on last run and interval
        },
        'trainer': {
            'status': 'active' if user['settings']['trainer'] else 'stopped',
            'tribe': user['travianCredentials']['tribe'] or 'Not set',
            'troops': [], # This would be retrieved from trainer configuration
        },
    }
    
    # Render dashboard template
    return render_template(
        'user/dashboard.html', 
        current_user=user,
        dashboard=dashboard_data,
        title='Dashboard'
    )


@user_bp.route('/profile', methods=['GET', 'POST'])
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


@user_bp.route('/travian-settings', methods=['GET', 'POST'])
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
    
    # Prepare travian settings data
    travian_settings = {
        'travian_credentials': {
            'username': user['travianCredentials'].get('username', ''),
            'password': '********' if user['travianCredentials'].get('password', '') else '',
            'server': user['travianCredentials'].get('server', ''),
            'tribe': user['travianCredentials'].get('tribe', '')
        },
        'last_connection': 'Never'  # This would be retrieved from activity logs
    }
    
    # Render travian settings template
    return render_template(
        'user/travian_settings.html', 
        user_profile=travian_settings,
        current_user=user, 
        title='Travian Settings'
    )


@user_bp.route('/villages')
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


@user_bp.route('/auto-farm')
@login_required
def auto_farm():
    """Auto farm management route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Check if user has subscription
    if user['subscription']['status'] != 'active':
        # Flash error message
        flash('You need an active subscription to use Auto Farm', 'warning')
        
        # Redirect to subscription page
        return redirect(url_for('user.subscription'))
    
    # Get subscription plan
    plan_model = SubscriptionPlan()
    plan = None
    if user['subscription']['planId']:
        plan = plan_model.get_plan_by_id(user['subscription']['planId'])
    
    # Check if auto farm is included in plan
    if not plan or not plan['features'].get('autoFarm', False):
        # Flash error message
        flash('Auto Farm is not included in your subscription plan', 'warning')
        
        # Redirect to subscription page
        return redirect(url_for('user.subscription'))
    
    # Prepare auto farm data
    auto_farm_data = {
        'status': 'active' if user['settings'].get('autoFarm', False) else 'stopped',
        'interval': 60,  # Default interval
        'last_run': 'Never',  # This would be retrieved from activity logs
        'next_run': 'N/A',  # This would be calculated based on last run and interval
        'villages': user['villages']
    }
    
    # Render auto farm template
    return render_template(
        'user/auto_farm.html', 
        auto_farm=auto_farm_data,
        current_user=user, 
        title='Auto Farm Management'
    )


@user_bp.route('/troop-trainer')
@login_required
def troop_trainer():
    """Troop trainer management route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Check if user has subscription
    if user['subscription']['status'] != 'active':
        # Flash error message
        flash('You need an active subscription to use Troop Trainer', 'warning')
        
        # Redirect to subscription page
        return redirect(url_for('user.subscription'))
    
    # Get subscription plan
    plan_model = SubscriptionPlan()
    plan = None
    if user['subscription']['planId']:
        plan = plan_model.get_plan_by_id(user['subscription']['planId'])
    
    # Check if troop trainer is included in plan
    if not plan or not plan['features'].get('trainer', False):
        # Flash error message
        flash('Troop Trainer is not included in your subscription plan', 'warning')
        
        # Redirect to subscription page
        return redirect(url_for('user.subscription'))
    
    # Prepare troop trainer data
    trainer_data = {
        'status': 'active' if user['settings'].get('trainer', False) else 'stopped',
        'tribe': user['travianCredentials'].get('tribe', 'Unknown'),
        'troops': [],  # This would be retrieved from trainer configuration
        'villages': user['villages']
    }
    
    # Render troop trainer template
    return render_template(
        'user/troop_trainer.html', 
        trainer=trainer_data,
        current_user=user, 
        title='Troop Trainer'
    )


@user_bp.route('/activity-logs')
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
    
    # Prepare activity logs data (example logs)
    activity_logs = [
        {
            'timestamp': '2025-03-13 15:30:45',
            'activity': 'Auto-Farm',
            'details': 'Sent farm lists from Main Village',
            'status': 'Success'
        },
        {
            'timestamp': '2025-03-13 14:15:22',
            'activity': 'Troop Training',
            'details': 'Trained 50 Legionnaires in Main Village',
            'status': 'Success'
        },
        {
            'timestamp': '2025-03-13 12:30:10',
            'activity': 'Auto-Farm',
            'details': 'Sent farm lists from Second Village',
            'status': 'Success'
        },
        {
            'timestamp': '2025-03-13 11:05:38',
            'activity': 'System',
            'details': 'Bot started after maintenance',
            'status': 'Info'
        },
        {
            'timestamp': '2025-03-13 10:45:15',
            'activity': 'System',
            'details': 'Scheduled maintenance began',
            'status': 'Warning'
        }
    ]
    
    # Render activity logs template
    return render_template(
        'user/activity_logs.html', 
        logs=activity_logs,
        current_user=user, 
        title='Activity Logs'
    )


@user_bp.route('/subscription')
@login_required
def subscription():
    """Subscription management route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get subscription plans
    plan_model = SubscriptionPlan()
    plans = plan_model.list_plans()
    
    # Get current plan
    current_plan = None
    if user['subscription']['planId']:
        current_plan = plan_model.get_plan_by_id(user['subscription']['planId'])
    
    # Render subscription template
    return render_template(
        'user/subscription.html', 
        plans=plans,
        current_plan=current_plan,
        current_user=user, 
        title='Subscription'
    )


@user_bp.route('/support')
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