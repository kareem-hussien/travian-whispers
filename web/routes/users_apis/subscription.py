"""
Subscription management routes for Travian Whispers web application.
"""
import logging
from datetime import datetime
from flask import (
    render_template, flash, session, redirect, url_for
)

from web.utils.decorators import login_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register subscription routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/subscription')(login_required(subscription))

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
    
    # Get subscription transaction history
    from database.models.transaction import Transaction
    transaction_model = Transaction()
    
    # Get transactions for this user
    transactions = transaction_model.get_user_transactions(session['user_id'])
    
    # Format transaction history
    transaction_history = []
    for tx in transactions:
        # Get plan info
        plan_info = plan_model.get_plan_by_id(tx.get('planId'))
        plan_name = plan_info['name'] if plan_info else 'Unknown Plan'
        
        transaction_history.append({
            'id': str(tx.get('_id')),
            'date': tx.get('createdAt').strftime('%Y-%m-%d'),
            'amount': tx.get('amount'),
            'plan': plan_name,
            'status': tx.get('status'),
            'payment_method': tx.get('paymentMethod')
        })
    
    # Get subscription statistics
    subscription_stats = {
        'total_spent': sum(tx.get('amount', 0) for tx in transactions),
        'subscription_age': (datetime.utcnow() - user['subscription'].get('startDate')).days if user['subscription'].get('startDate') else 0,
        'transactions_count': len(transactions),
        'next_payment': user['subscription'].get('endDate').strftime('%Y-%m-%d') if user['subscription'].get('endDate') else 'N/A'
    }
    
    # Render subscription template
    return render_template(
        'user/subscription.html', 
        plans=plans,
        current_plan=current_plan,
        transaction_history=transaction_history,
        subscription_stats=subscription_stats,
        current_user=user, 
        title='Subscription'
    )
