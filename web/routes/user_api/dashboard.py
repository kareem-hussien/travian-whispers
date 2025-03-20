"""
Dashboard routes for user dashboard.
This module defines the route for the main dashboard page.
"""
import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.activity import UserActivity
from database.models.village import Village
from database.models.auto_farm import AutoFarm
from database.models.trainer import TroopTrainer

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/')
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