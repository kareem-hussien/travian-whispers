"""
Auto Farm routes for user dashboard.
This module defines the routes for auto farm management.
"""
import logging
from flask import render_template, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.auto_farm import AutoFarm
from database.models.village import Village

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/auto-farm')
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