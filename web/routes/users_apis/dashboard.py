"""
User dashboard routes for Travian Whispers web application.
"""
import logging
from flask import (
    render_template, flash, session, redirect, url_for
)

from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register dashboard routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/')(login_required(dashboard))

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
    
    # Get user activity logs for auto-farm and trainer
    from database.models.activity_log import ActivityLog
    activity_model = ActivityLog()
    
    # Get latest auto-farm activity
    auto_farm_log = activity_model.get_latest_user_activity(
        user_id=session['user_id'],
        activity_type='auto-farm'
    )
    
    # Get latest trainer activity
    trainer_log = activity_model.get_latest_user_activity(
        user_id=session['user_id'],
        activity_type='troop-training'
    )
    
    # Get trainer configuration
    from database.models.trainer import TrainerConfiguration
    trainer_model = TrainerConfiguration()
    trainer_config = trainer_model.get_user_configuration(session['user_id'])
    
    # Calculate next auto-farm run time
    next_run_time = 'Not scheduled'
    if user['settings'].get('autoFarm', False) and auto_farm_log:
        from datetime import datetime, timedelta
        # Use interval from settings or default to 60 minutes
        interval_minutes = user.get('autoFarmInterval', 60)
        if auto_farm_log.get('timestamp'):
            next_run = auto_farm_log['timestamp'] + timedelta(minutes=interval_minutes)
            if next_run > datetime.now():
                next_run_time = next_run.strftime('%Y-%m-%d %H:%M')
            else:
                next_run_time = 'Pending'
    
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
            'status': 'active' if user['settings'].get('autoFarm', False) else 'stopped',
            'last_run': auto_farm_log['timestamp'].strftime('%Y-%m-%d %H:%M') if auto_farm_log and auto_farm_log.get('timestamp') else 'Never',
            'next_run': next_run_time,
        },
        'trainer': {
            'status': 'active' if user['settings'].get('trainer', False) else 'stopped',
            'tribe': user['travianCredentials'].get('tribe', '') or 'Not set',
            'troops': trainer_config.get('troops', []) if trainer_config else [],
        },
    }
    
    # Render dashboard template
    return render_template(
        'user/dashboard.html', 
        current_user=user,
        dashboard=dashboard_data,
        title='Dashboard'
    )
