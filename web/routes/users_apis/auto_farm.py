"""
Auto farm management routes for Travian Whispers web application.
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
    """Register auto farm routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/auto-farm')(login_required(auto_farm))

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
    
    # Get auto-farm activity logs
    from database.models.activity_log import ActivityLog
    activity_model = ActivityLog()
    
    # Get latest auto-farm activity
    auto_farm_log = activity_model.get_latest_user_activity(
        user_id=session['user_id'],
        activity_type='auto-farm'
    )
    
    # Get auto-farm configuration
    from database.models.auto_farm import AutoFarmConfiguration
    auto_farm_model = AutoFarmConfiguration()
    auto_farm_config = auto_farm_model.get_user_configuration(session['user_id'])
    
    # Calculate next run time
    next_run_time = 'Not scheduled'
    if user['settings'].get('autoFarm', False) and auto_farm_log:
        from datetime import datetime, timedelta
        # Get interval from configuration or use default
        interval_minutes = auto_farm_config.get('interval', 60) if auto_farm_config else 60
        if auto_farm_log.get('timestamp'):
            next_run = auto_farm_log['timestamp'] + timedelta(minutes=interval_minutes)
            if next_run > datetime.now():
                next_run_time = next_run.strftime('%Y-%m-%d %H:%M')
            else:
                next_run_time = 'Pending'
    
    # Prepare auto farm data
    auto_farm_data = {
        'status': 'active' if user['settings'].get('autoFarm', False) else 'stopped',
        'interval': auto_farm_config.get('interval', 60) if auto_farm_config else 60,
        'last_run': auto_farm_log['timestamp'].strftime('%Y-%m-%d %H:%M') if auto_farm_log and auto_farm_log.get('timestamp') else 'Never',
        'next_run': next_run_time,
        'villages': user['villages'],
        'farm_lists': auto_farm_config.get('farmLists', []) if auto_farm_config else []
    }
    
    # Render auto farm template
    return render_template(
        'user/auto_farm.html', 
        auto_farm=auto_farm_data,
        current_user=user, 
        title='Auto Farm Management'
    )
