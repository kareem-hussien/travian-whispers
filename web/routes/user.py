"""
User routes for Travian Whispers web application.
This module defines the blueprint for user dashboard routes.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.activity import UserActivity
from database.models.village import Village
from database.models.auto_farm import AutoFarm
from database.models.trainer import TroopTrainer

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
    
    # Get support articles from config (if available)
    support_articles = current_app.config.get('SUPPORT_ARTICLES', [])
    
    # Get FAQ entries from database (if available)
    try:
        from database.models.faq import FAQ
        faq_model = FAQ()
        faq_entries = faq_model.list_faq_entries()
    except (ImportError, AttributeError):
        # Fall back to empty list if model doesn't exist
        faq_entries = []
    
    # Render support template
    return render_template(
        'user/support.html', 
        current_user=user,
        support_articles=support_articles,
        faq_entries=faq_entries,
        title='Help & Support'
    ) found', 'danger')
        
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
    
    # Get trainer data from database
    trainer_model = TroopTrainer()
    trainer_data = trainer_model.get_user_config(session['user_id'])
    
    # If no trainer data exists, initialize with defaults
    if not trainer_data:
        trainer_data = {
            'status': 'stopped',
            'tribe': user['travianCredentials'].get('tribe', 'Unknown'),
            'troops': [],
        }
    
    # Get villages from database
    village_model = Village()
    trainer_data['villages'] = village_model.get_user_villages(session['user_id'])
    
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
    
    # Get subscription plan
    plan_model = SubscriptionPlan()
    plan = None
    if user['subscription']['planId']:
        plan = plan_model.get_plan_by_id(user['subscription']['planId'])
    
    # Get user's villages from database
    village_model = Village()
    user_villages = village_model.get_user_villages(session['user_id'])
    
    # Get auto farm status from database
    auto_farm_model = AutoFarm()
    auto_farm_status = auto_farm_model.get_user_status(session['user_id'])
    
    # If no auto farm status exists, initialize with defaults
    if not auto_farm_status:
        auto_farm_status = {
            'status': 'stopped',
            'last_run': None,
            'next_run': None
        }
    
    # Calculate next run if active
    if auto_farm_status['status'] == 'active' and auto_farm_status['last_run']:
        last_run = auto_farm_status['last_run']
        if isinstance(last_run, str):
            try:
                last_run = datetime.strptime(last_run, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                last_run = datetime.now() - timedelta(hours=1)
        
        # Get interval from settings or default to 60 minutes
        interval_minutes = user.get('settings', {}).get('autoFarmInterval', 60)
        next_run = last_run + timedelta(minutes=interval_minutes)
        
        # Format for display
        auto_farm_status['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')
    else:
        auto_farm_status['next_run'] = 'N/A'
    
    # Format last run time
    if auto_farm_status['last_run']:
        if isinstance(auto_farm_status['last_run'], datetime):
            auto_farm_status['last_run'] = auto_farm_status['last_run'].strftime('%Y-%m-%d %H:%M:%S')
    else:
        auto_farm_status['last_run'] = 'Never'
    
    # Get troop trainer status from database
    trainer_model = TroopTrainer()
    trainer_status = trainer_model.get_user_status(session['user_id'])
    
    # If no trainer status exists, initialize with defaults
    if not trainer_status:
        trainer_status = {
            'status': 'stopped',
            'tribe': user['travianCredentials'].get('tribe', ''),
            'troops': []
        }
    
    # Get latest activity logs for the user
    activity_model = UserActivity()
    recent_activities = activity_model.get_recent_activities(session['user_id'], limit=5)
    
    # Prepare data for dashboard
    dashboard_data = {
        'username': user['username'],
        'email': user['email'],
        'subscription': {
            'status': user['subscription']['status'],
            'plan': plan['name'] if plan else 'None',
            'start_date': user['subscription'].get('startDate'),
            'end_date': user['subscription'].get('endDate'),
        },
        'villages': user_villages,
        'auto_farm': {
            'status': auto_farm_status['status'],
            'last_run': auto_farm_status['last_run'],
            'next_run': auto_farm_status['next_run'],
        },
        'trainer': {
            'status': trainer_status['status'],
            'tribe': trainer_status['tribe'] or 'Not set',
            'troops': trainer_status['troops'],
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
    
    # Get auto farm data from database
    auto_farm_model = AutoFarm()
    auto_farm_data = auto_farm_model.get_user_config(session['user_id'])
    
    # If no auto farm data exists, initialize with defaults
    if not auto_farm_data:
        auto_farm_data = {
            'status': 'stopped',
            'interval': 60,
            'last_run': 'Never',
            'next_run': 'N/A',
        }
    
    # Get villages from database
    village_model = Village()
    auto_farm_data['villages'] = village_model.get_user_villages(session['user_id'])
    
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
        flash('User not