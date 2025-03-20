"""
Transaction management routes for Travian Whispers admin panel.
This module defines the transaction management routes for the admin panel.
"""
import logging
from flask import render_template, request, redirect, url_for, flash, session
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.transaction import Transaction
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

@admin_required
def index():
    """Transaction history page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Initialize models
    transaction_model = Transaction()
    subscription_model = SubscriptionPlan()
    
    # Fetch all transactions
    transactions_cursor = transaction_model.collection.find().sort("createdAt", -1)
    transactions = []
    
    for tx in transactions_cursor:
        # Get user
        user = user_model.get_user_by_id(str(tx["userId"]))
        username = user["username"] if user else "Unknown User"
        
        # Get plan
        plan = subscription_model.get_plan_by_id(str(tx["planId"]))
        plan_name = plan["name"] if plan else "Unknown Plan"
        
        # Format for template
        transactions.append({
            'id': tx["_id"],
            'user': username,
            'plan': plan_name,
            'amount': f"${tx['amount']}",
            'date': tx["createdAt"].strftime('%Y-%m-%d'),
            'status': tx["status"]
        })
    
    # Filter transactions based on query parameters
    status_filter = request.args.get('status')
    plan_filter = request.args.get('plan')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_query = request.args.get('q')
    
    filtered_transactions = transactions
    
    if status_filter:
        filtered_transactions = [tx for tx in filtered_transactions if tx['status'] == status_filter]
    
    if plan_filter:
        filtered_transactions = [tx for tx in filtered_transactions if tx['plan'] == plan_filter]
    
    if search_query:
        filtered_transactions = [
            tx for tx in filtered_transactions 
            if (search_query.lower() in tx['user'].lower() or 
                search_query.lower() in str(tx['id']).lower())
        ]
    
    # Render transactions template
    return render_template(
        'admin/transactions.html', 
        transactions=filtered_transactions, 
        current_user=current_user,
        title='Transaction History'
    )

@admin_required
def details(transaction_id):
    """Transaction details page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Initialize models
    transaction_model = Transaction()
    subscription_model = SubscriptionPlan()
    
    # Fetch transaction
    tx = transaction_model.get_transaction(transaction_id)
    
    if not tx:
        flash('Transaction not found', 'danger')
        return redirect(url_for('admin.transactions'))
    
    # Get user
    user = user_model.get_user_by_id(str(tx["userId"]))
    username = user["username"] if user else "Unknown User"
    email = user["email"] if user else "Unknown Email"
    
    # Get plan
    plan = subscription_model.get_plan_by_id(str(tx["planId"]))
    plan_name = plan["name"] if plan else "Unknown Plan"
    
    # Format for template
    transaction = {
        'id': tx["_id"],
        'user': username,
        'user_id': tx["userId"],
        'user_email': email,
        'plan': plan_name,
        'amount': f"${tx['amount']}",
        'date': tx["createdAt"].strftime('%Y-%m-%d'),
        'status': tx["status"],
        'payment_method': tx["paymentMethod"],
        'payment_id': tx["paymentId"],
        'billing_period': tx["billingPeriod"],
        'subscription_start': user["subscription"].get("startDate") if user else None,
        'subscription_end': user["subscription"].get("endDate") if user else None
    }
    
    # Get gateway response from payment provider
    payment_gateway = tx.get("paymentGateway", {})
    
    # Render transaction details template
    return render_template(
        'admin/transaction_details.html', 
        transaction=transaction,
        payment_gateway=payment_gateway,
        current_user=current_user,
        title='Transaction Details'
    )

@admin_required
def update_status(transaction_id):
    """Update transaction status."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get new status
    status = request.form.get('status')
    
    if not status or status not in ['completed', 'pending', 'failed', 'refunded']:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin.transaction_details', transaction_id=transaction_id))
    
    # Update transaction status
    transaction_model = Transaction()
    success = transaction_model.update_transaction_status(transaction_id, status)
    
    if not success:
        flash('Failed to update transaction status', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to update transaction status")
        return redirect(url_for('admin.transaction_details', transaction_id=transaction_id))
    
    # Handle subscription changes if necessary
    if status == 'completed':
        # Update user subscription if transaction was just completed
        from payment.paypal import process_successful_payment
        process_successful_payment(transaction_model.get_transaction(transaction_id)["paymentId"])
    elif status == 'refunded' or status == 'failed':
        # Cancel user subscription if transaction was refunded or failed
        tx = transaction_model.get_transaction(transaction_id)
        user_model.update_subscription_status(str(tx["userId"]), "inactive")
    
    flash('Transaction status updated successfully', 'success')
    logger.info(f"Admin '{current_user['username']}' updated transaction status to '{status}'")
    return redirect(url_for('admin.transaction_details', transaction_id=transaction_id))