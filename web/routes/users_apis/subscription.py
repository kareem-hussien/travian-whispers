"""
Enhanced subscription management routes for Travian Whispers web application.
This module provides the subscription management functionality.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, flash, session, redirect, 
    url_for, request, jsonify, current_app
)
from bson import ObjectId

from web.utils.decorators import login_required, api_error_handler
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from database.models.activity_log import ActivityLog
from payment.paypal import create_subscription_order, process_successful_payment

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register subscription routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/subscription')(login_required(subscription))
    user_bp.route('/subscription/success')(login_required(subscription_success))
    user_bp.route('/subscription/cancel')(login_required(subscription_cancel))
    
    # API endpoints for subscription management
    user_bp.route('/api/subscription/create-order', methods=['POST'])(
        api_error_handler(login_required(create_subscription_order_api))
    )
    user_bp.route('/api/subscription/cancel', methods=['POST'])(
        api_error_handler(login_required(cancel_subscription_api))
    )

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
    
    # Get user's transaction history
    transaction_model = Transaction()
    transactions = transaction_model.get_user_transactions(session['user_id'])
    
    # Format transaction history for display
    transaction_history = []
    for tx in transactions:
        # Get plan info
        plan_info = plan_model.get_plan_by_id(tx.get('planId'))
        plan_name = plan_info['name'] if plan_info else 'Unknown Plan'
        
        transaction_history.append({
            'id': str(tx.get('_id')),
            'date': tx.get('createdAt').strftime('%Y-%m-%d') if tx.get('createdAt') else 'Unknown',
            'amount': tx.get('amount'),
            'plan': plan_name,
            'status': tx.get('status'),
            'payment_method': tx.get('paymentMethod')
        })
    
    # Calculate subscription statistics
    subscription_stats = {
        'status': user['subscription']['status'],
        'start_date': user['subscription'].get('startDate').strftime('%Y-%m-%d') if user['subscription'].get('startDate') else 'N/A',
        'end_date': user['subscription'].get('endDate').strftime('%Y-%m-%d') if user['subscription'].get('endDate') else 'N/A',
        'total_spent': sum(tx.get('amount', 0) for tx in transactions),
        'transactions_count': len(transactions),
        'next_payment': user['subscription'].get('endDate').strftime('%Y-%m-%d') if user['subscription'].get('endDate') else 'N/A'
    }
    
    # Calculate subscription age safely
    start_date = user['subscription'].get('startDate')
    if start_date:
        try:
            # Simply use .days attribute which handles timezone differences
            # as long as both dates are in the same timezone (UTC)
            now = datetime.utcnow()
            delta = now - start_date
            subscription_stats['subscription_age'] = delta.days
        except TypeError:
            # If there's a timezone mismatch, convert to string and parse to ensure both are naive
            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            start_date_naive = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
            now = datetime.utcnow()
            delta = now - start_date_naive
            subscription_stats['subscription_age'] = delta.days
    else:
        subscription_stats['subscription_age'] = 0
    
    # Log a view activity
    activity_model = ActivityLog()
    activity_model.log_activity(
        user_id=session['user_id'],
        activity_type='subscription-view',
        details='Viewed subscription management page',
        status='info'
    )
    
    # Render subscription template
    return render_template(
        'user/subscription.html', 
        plans=plans,
        current_plan=current_plan,
        transaction_history=transaction_history,
        subscription_stats=subscription_stats,
        current_user=user, 
        title='Subscription Management'
    )

@login_required
def subscription_success():
    """Handle successful subscription payment."""
    # Get payment details from query parameters
    order_id = request.args.get('token')
    payer_id = request.args.get('PayerID')
    
    if not order_id or not payer_id:
        flash('Invalid payment parameters', 'danger')
        return redirect(url_for('user.subscription'))
    
    # Process the successful payment
    success = process_successful_payment(order_id)
    
    if success:
        # Flash success message
        flash('Your subscription has been successfully activated!', 'success')
        
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='subscription-payment',
            details=f'Successfully processed payment for subscription (Order ID: {order_id})',
            status='success'
        )
    else:
        # Flash error message
        flash('Failed to process payment. Please contact support if your subscription is not activated.', 'danger')
        
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='subscription-payment',
            details=f'Failed to process payment for subscription (Order ID: {order_id})',
            status='error'
        )
    
    # Redirect to subscription page
    return redirect(url_for('user.subscription'))

@login_required
def subscription_cancel():
    """Handle cancelled subscription payment."""
    # Flash info message
    flash('Subscription payment was cancelled.', 'info')
    
    # Log the activity
    activity_model = ActivityLog()
    activity_model.log_activity(
        user_id=session['user_id'],
        activity_type='subscription-payment',
        details='Payment process was cancelled by user',
        status='info'
    )
    
    # Redirect to subscription page
    return redirect(url_for('user.subscription'))

@api_error_handler
@login_required
def create_subscription_order_api():
    """API endpoint to create a PayPal order for subscription payment."""
    # Get user ID
    user_id = session['user_id']
    
    # Get request data
    data = request.get_json()
    plan_id = data.get('planId')
    
    if not plan_id:
        return jsonify({
            'success': False,
            'message': 'Plan ID is required'
        }), 400
    
    # Validate plan exists
    plan_model = SubscriptionPlan()
    plan = plan_model.get_plan_by_id(plan_id)
    
    if not plan:
        return jsonify({
            'success': False,
            'message': 'Invalid plan ID'
        }), 400
    
    # Generate success and cancel URLs
    base_url = request.host_url.rstrip('/')
    success_url = f"{base_url}/dashboard/subscription/success"
    cancel_url = f"{base_url}/dashboard/subscription/cancel"
    
    # Create PayPal order
    success, order_id, approval_url = create_subscription_order(
        plan_id, 
        user_id, 
        success_url, 
        cancel_url
    )
    
    if success and order_id and approval_url:
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='subscription-order',
            details=f'Created subscription order for plan {plan["name"]} (Order ID: {order_id})',
            status='success'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'orderId': order_id,
                'approvalUrl': approval_url
            }
        })
    else:
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='subscription-order',
            details=f'Failed to create subscription order for plan {plan["name"]}',
            status='error'
        )
        
        return jsonify({
            'success': False,
            'message': 'Failed to create subscription order'
        }), 500

@api_error_handler
@login_required
def cancel_subscription_api():
    """API endpoint to cancel a subscription."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Check if user has an active subscription
    if user['subscription']['status'] != 'active':
        return jsonify({
            'success': False,
            'message': 'No active subscription to cancel'
        }), 400
    
    # Update subscription status to cancelled
    update_data = {
        'subscription': {
            'status': 'cancelled',
            'planId': user['subscription']['planId'],
            'startDate': user['subscription']['startDate'],
            'endDate': user['subscription']['endDate']
        }
    }
    
    if user_model.update_user(session['user_id'], update_data):
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='subscription-cancel',
            details='Cancelled subscription',
            status='success'
        )
        
        # Also update user settings to disable auto-renew
        settings_update = {
            'settings': {
                'autoFarm': user['settings'].get('autoFarm', False),
                'trainer': user['settings'].get('trainer', False),
                'notification': user['settings'].get('notification', True),
                'autoRenew': False
            }
        }
        
        user_model.update_user(session['user_id'], settings_update)
        
        return jsonify({
            'success': True,
            'message': 'Subscription cancelled successfully'
        })
    else:
        # Log the activity
        activity_model = ActivityLog()
        activity_model.log_activity(
            user_id=session['user_id'],
            activity_type='subscription-cancel',
            details='Failed to cancel subscription',
            status='error'
        )
        
        return jsonify({
            'success': False,
            'message': 'Failed to cancel subscription'
        }), 500