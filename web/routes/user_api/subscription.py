"""
Subscription routes for user dashboard.
This module defines the routes for subscription management.
"""
import logging
from flask import render_template, redirect, url_for, flash, session
from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(bp):
    """Register routes with blueprint."""
    
    @bp.route('/subscription')
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