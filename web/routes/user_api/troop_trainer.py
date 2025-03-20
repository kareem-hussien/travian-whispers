"""
Troop Trainer routes for user dashboard.
This module defines the routes for troop trainer management.
"""
import logging
from flask import render_template, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.trainer import TroopTrainer
from database.models.village import Village

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/troop-trainer')
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