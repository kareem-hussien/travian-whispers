"""
Troop trainer management routes for Travian Whispers web application.
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
    """Register troop trainer routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/troop-trainer')(login_required(troop_trainer))

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
    
    # Get training activity logs
    from database.models.activity_log import ActivityLog
    activity_model = ActivityLog()
    
    # Get latest training activity
    training_log = activity_model.get_latest_user_activity(
        user_id=session['user_id'],
        activity_type='troop-training'
    )
    
    # Get trainer configuration
    from database.models.trainer import TrainerConfiguration
    trainer_model = TrainerConfiguration()
    trainer_config = trainer_model.get_user_configuration(session['user_id'])
    
    # Get tribe-specific troop types
    from database.models.tribe import TribeData
    tribe_model = TribeData()
    tribe = user['travianCredentials'].get('tribe', 'Unknown')
    troop_types = tribe_model.get_troop_types(tribe)
    
    # Prepare troop training configuration
    troops = []
    if trainer_config and trainer_config.get('troops'):
        troops = trainer_config['troops']
    elif troop_types:
        # Create default configuration based on tribe
        troops = [{'type': troop, 'priority': i + 1, 'target': 0, 'enabled': False} 
                 for i, troop in enumerate(troop_types)]
    
    # Prepare troop trainer data
    trainer_data = {
        'status': 'active' if user['settings'].get('trainer', False) else 'stopped',
        'tribe': user['travianCredentials'].get('tribe', 'Unknown'),
        'troops': troops,
        'villages': user['villages'],
        'last_training': training_log['timestamp'].strftime('%Y-%m-%d %H:%M') if training_log and training_log.get('timestamp') else 'Never',
        'training_queue': trainer_config.get('queue', []) if trainer_config else []
    }
    
    # Render troop trainer template
    return render_template(
        'user/troop_trainer.html', 
        trainer=trainer_data,
        current_user=user, 
        title='Troop Trainer'
    )
