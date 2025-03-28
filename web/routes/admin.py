"""
Admin routes for Travian Whispers web application.
This module defines the blueprint for admin panel routes.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from database.backup import create_backup

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard route."""
    # Initialize models
    user_model = User()
    subscription_model = SubscriptionPlan()
    transaction_model = Transaction()
    
    # Calculate user statistics
    total_users = user_model.collection.count_documents({})
    active_users = user_model.collection.count_documents({"subscription.status": "active"})
    
    # Get new users this week
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = user_model.collection.count_documents({"createdAt": {"$gte": one_week_ago}})
    
    # Calculate revenue statistics
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Get current month revenue
    revenue_pipeline = [
        {"$match": {
            "createdAt": {"$gte": current_month_start},
            "status": "completed"
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$amount"}
        }}
    ]
    current_revenue = list(transaction_model.collection.aggregate(revenue_pipeline))
    monthly_revenue = current_revenue[0]["total"] if current_revenue else 0
    
    # Get previous month revenue for comparison
    prev_revenue_pipeline = [
        {"$match": {
            "createdAt": {"$gte": previous_month_start, "$lt": current_month_start},
            "status": "completed"
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$amount"}
        }}
    ]
    prev_revenue = list(transaction_model.collection.aggregate(prev_revenue_pipeline))
    prev_monthly_revenue = prev_revenue[0]["total"] if prev_revenue else 0
    
    # Calculate percentage change
    if prev_monthly_revenue > 0:
        monthly_change = ((monthly_revenue - prev_monthly_revenue) / prev_monthly_revenue) * 100
    else:
        monthly_change = 0
    
    # Determine monthly goal (simplified to 25% more than current)
    monthly_goal = monthly_revenue * 1.25 if monthly_revenue > 0 else 15000
    
    # Subscription statistics
    active_subscriptions = user_model.collection.count_documents({"subscription.status": "active"})
    new_subscriptions = transaction_model.collection.count_documents({
        "createdAt": {"$gte": one_week_ago},
        "type": "subscription",
        "status": "completed"
    })
    
    # Get plan distribution
    basic_plan = subscription_model.get_plan_by_name("Basic")
    standard_plan = subscription_model.get_plan_by_name("Standard")
    premium_plan = subscription_model.get_plan_by_name("Premium")
    
    basic_count = user_model.collection.count_documents({
        "subscription.status": "active", 
        "subscription.planId": basic_plan["_id"] if basic_plan else None
    })
    
    standard_count = user_model.collection.count_documents({
        "subscription.status": "active", 
        "subscription.planId": standard_plan["_id"] if standard_plan else None
    })
    
    premium_count = user_model.collection.count_documents({
        "subscription.status": "active", 
        "subscription.planId": premium_plan["_id"] if premium_plan else None
    })
    
    # System status (simplified)
    system_stats = {
        "status": "Healthy",
        "uptime": "24d 12h 36m",  # Would be calculated from server start time
        "memory_usage": 62,        # Would be from system monitoring
        "maintenance_mode": False,
        "maintenance_message": "We are currently performing scheduled maintenance. Please check back later."
    }
    
    # Recent activity logs
    recent_activity = [
        {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "username": "admin",
            "action": "System backup created",
            "status": "Success",
            "status_class": "bg-success"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
            "username": "john_doe",
            "action": "Premium subscription purchased",
            "status": "Success",
            "status_class": "bg-success"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M'),
            "username": "jane_smith",
            "action": "Password reset requested",
            "status": "Pending",
            "status_class": "bg-warning"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M'),
            "username": "user123",
            "action": "Failed login attempt",
            "status": "Failed",
            "status_class": "bg-danger"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M'),
            "username": "new_user",
            "action": "Account created",
            "status": "Success",
            "status_class": "bg-success"
        }
    ]
    
    # Get recent users
    recent_users_cursor = user_model.collection.find().sort("createdAt", -1).limit(4)
    recent_users = []
    
    for user in recent_users_cursor:
        status = "Active" if user.get("isVerified", False) else "Pending"
        status_class = "bg-success" if status == "Active" else "bg-warning"
        
        recent_users.append({
            "id": user["_id"],
            "username": user["username"],
            "email": user["email"],
            "status": status,
            "status_class": status_class
        })
    
    # Get recent transactions
    recent_transactions_cursor = transaction_model.collection.find().sort("createdAt", -1).limit(5)
    recent_transactions = []
    
    for tx in recent_transactions_cursor:
        # Get plan name
        plan = subscription_model.get_plan_by_id(tx["planId"])
        plan_name = plan["name"] if plan else "Unknown Plan"
        
        # Get username
        user = user_model.get_user_by_id(tx["userId"])
        username = user["username"] if user else "Unknown User"
        
        # Format status class
        status_class = "bg-success"
        if tx["status"] == "pending":
            status_class = "bg-warning"
        elif tx["status"] == "failed":
            status_class = "bg-danger"
        
        recent_transactions.append({
            "id": tx["_id"],
            "username": username,
            "plan": plan_name,
            "amount": tx["amount"],
            "date": tx["createdAt"].strftime('%Y-%m-%d'),
            "status": tx["status"].capitalize(),
            "status_class": status_class
        })
    
    # Prepare data for the template
    user_stats = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_week': new_users_week
    }
    
    revenue_stats = {
        'monthly_revenue': monthly_revenue,
        'monthly_change': monthly_change,
        'monthly_goal': monthly_goal
    }
    
    subscription_stats = {
        'active_subscriptions': active_subscriptions,
        'new_subscriptions': new_subscriptions,
        'plan_distribution': {
            'basic': basic_count,
            'standard': standard_count,
            'premium': premium_count
        }
    }
    
    # Get current user for the template
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Render admin dashboard template
    return render_template(
        'admin/dashboard.html',
        user_stats=user_stats,
        revenue_stats=revenue_stats,
        subscription_stats=subscription_stats,
        system_stats=system_stats,
        recent_activity=recent_activity,
        recent_users=recent_users,
        recent_transactions=recent_transactions,
        current_user=current_user,
        title='Admin Dashboard'
    )


@admin_bp.route('/users')
@admin_required
def users():
    """User management page."""
    # Initialize user model
    user_model = User()
    
    # Fetch all users from database
    users_cursor = user_model.collection.find()
    users = []
    
    for user in users_cursor:
        # Get subscription info
        subscription_status = user["subscription"]["status"]
        plan_id = user["subscription"].get("planId")
        
        subscription_plan = "None"
        if plan_id:
            plan_model = SubscriptionPlan()
            plan = plan_model.get_plan_by_id(plan_id)
            if plan:
                subscription_plan = plan["name"]
        
        # Format for template
        users.append({
            'id': user["_id"],
            'username': user["username"],
            'email': user["email"],
            'role': user["role"],
            'status': "active" if user.get("isVerified", False) else "inactive",
            'subscription': subscription_plan,
            'joined': user["createdAt"].strftime('%Y-%m-%d'),
            'verified': user.get("isVerified", False),
            'last_login': user.get("lastLoginAt", "Never")
        })
    
    # Filter users based on query parameters
    status_filter = request.args.get('status')
    role_filter = request.args.get('role')
    search_query = request.args.get('q')
    
    filtered_users = users
    
    if status_filter:
        filtered_users = [user for user in filtered_users if user['status'] == status_filter]
    
    if role_filter:
        filtered_users = [user for user in filtered_users if user['role'] == role_filter]
    
    if search_query:
        filtered_users = [
            user for user in filtered_users 
            if search_query.lower() in user['username'].lower() or search_query.lower() in user['email'].lower()
        ]
    
    # Get current user for the template
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Render user management template
    return render_template(
        'admin/users.html', 
        users=filtered_users, 
        current_user=current_user,
        title='User Management'
    )


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def user_create():
    """Create user page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        # Process form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template(
                'admin/users/create.html', 
                current_user=current_user,
                title='Create User'
            )
        
        # Create user
        user_model = User()
        user = user_model.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            verification_token=None  # Admin-created users don't need verification
        )
        
        if user:
            # Mark as verified since admin is creating
            user_model.verify_user_by_id(str(user["_id"]))
            flash('User created successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' created user '{username}'")
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to create user. Username or email may already exist.', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to create user '{username}'")
    
    # Render user create template
    return render_template(
        'admin/users/create.html', 
        current_user=current_user,
        title='Create User'
    )

@admin_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    """Edit user page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get user to edit
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        # Process form data
        email = request.form.get('email')
        role = request.form.get('role')
        status = request.form.get('status')
        
        # Prepare update data
        update_data = {
            'email': email,
            'role': role,
            'isVerified': status == 'active'
        }
        
        # Process password change if provided
        new_password = request.form.get('new_password')
        
        # Update user
        success = user_model.update_user(user_id, update_data)

        if success:
            # Handle password change separately if needed
            if new_password:
                # In a real implementation, this would hash the password
                if not user_model.admin_reset_password(user_id, new_password):
                    flash('Failed to update password', 'warning')
                    logger.warning(f"Admin '{current_user['username']}' failed to update password for user '{user['username']}'")
            
            flash('User updated successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' updated user '{user['username']}'")
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to update user', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to update user '{user['username']}'")
    
    # Format for template
    formatted_user = {
        'id': user["_id"],
        'username': user["username"],
        'email': user["email"],
        'role': user["role"],
        'status': "active" if user.get("isVerified", False) else "inactive",
        'joined': user["createdAt"].strftime('%Y-%m-%d'),
        'last_login': user.get("lastLoginAt", "Never")
    }
    
    # Render user edit template
    return render_template(
        'admin/users/edit.html', 
        user=formatted_user, 
        current_user=current_user,
        title='Edit User'
    )


@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@admin_required
def user_delete(user_id):
    """Delete user."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get user to delete
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent self-deletion
    if str(user["_id"]) == session['user_id']:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    # Delete user
    success = user_model.delete_user(user_id)
    
    if success:
        flash('User deleted successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' deleted user '{user['username']}'")
    else:
        flash('Failed to delete user', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to delete user '{user['username']}'")
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/subscriptions')
@admin_required
def subscriptions():
    """Subscription plans management page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get subscription plans
    subscription_model = SubscriptionPlan()
    plans = subscription_model.list_plans()
    
    # Add user count and revenue to each plan
    for plan in plans:
        # Count users with this plan
        plan_id = plan["_id"]
        user_count = user_model.collection.count_documents({
            "subscription.planId": plan_id,
            "subscription.status": "active"
        })
        
        # Calculate monthly revenue
        monthly_revenue = user_count * plan["price"]["monthly"]
        
        # Add to plan object
        plan["users"] = user_count
        plan["revenue"] = monthly_revenue
        
        # Format price for display
        plan["price"] = f"${plan['price']['monthly']}"
    
    # Render subscription plans template
    return render_template(
        'admin/subscriptions.html', 
        plans=plans, 
        current_user=current_user,
        title='Subscription Plans'
    )


@admin_bp.route('/subscriptions/create', methods=['GET', 'POST'])
@admin_required
def create_plan():
    """Create subscription plan page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        # Process form submission
        name = request.form.get('planName')
        monthly_price = float(request.form.get('planPrice', 0))
        yearly_price = float(request.form.get('yearlyPrice', 0))
        description = request.form.get('planDescription')
        
        # Get features
        features = {
            'autoFarm': 'featureAutoFarm' in request.form,
            'trainer': 'featureTrainer' in request.form,
            'notification': 'featureNotification' in request.form,
            'advanced': 'featureAdvanced' in request.form,
            'maxVillages': int(request.form.get('maxVillages', 1)),
            'maxTasks': int(request.form.get('maxTasks', 1))
        }
        
        # Create new plan
        subscription_model = SubscriptionPlan()
        new_plan = subscription_model.create_plan(
            name=name,
            description=description,
            monthly_price=monthly_price,
            yearly_price=yearly_price,
            features=features
        )
        
        if new_plan:
            flash('Subscription plan created successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' created subscription plan '{name}'")
            return redirect(url_for('admin.subscriptions'))
        else:
            flash('Failed to create plan. Name may already exist.', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to create subscription plan '{name}'")
    
    # Render plan create template
    return render_template(
        'admin/subscriptions/create.html', 
        current_user=current_user,
        title='Create Subscription Plan'
    )


@admin_bp.route('/subscriptions/edit/<plan_id>', methods=['GET', 'POST'])
@admin_required
def edit_plan(plan_id):
    """Edit subscription plan page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get subscription plan
    subscription_model = SubscriptionPlan()
    plan = subscription_model.get_plan_by_id(plan_id)
    
    if not plan:
        flash('Plan not found', 'danger')
        return redirect(url_for('admin.subscriptions'))
    
    if request.method == 'POST':
        # Process form submission
        name = request.form.get('planName')
        monthly_price = float(request.form.get('planPrice', 0))
        yearly_price = float(request.form.get('yearlyPrice', 0))
        description = request.form.get('planDescription')
        
        # Get features
        features = {
            'autoFarm': 'featureAutoFarm' in request.form,
            'trainer': 'featureTrainer' in request.form,
            'notification': 'featureNotification' in request.form,
            'advanced': 'featureAdvanced' in request.form,
            'maxVillages': int(request.form.get('maxVillages', 1)),
            'maxTasks': int(request.form.get('maxTasks', 1))
        }
        
        # Prepare update data
        update_data = {
            'name': name,
            'description': description,
            'price': {
                'monthly': monthly_price,
                'yearly': yearly_price
            },
            'features': features
        }
        
        # Update plan
        success = subscription_model.update_plan(plan_id, update_data)
        
        if success:
            flash('Subscription plan updated successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' updated subscription plan '{name}'")
            return redirect(url_for('admin.subscriptions'))
        else:
            flash('Failed to update plan', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to update subscription plan '{name}'")
    
    # Render plan edit template
    return render_template(
        'admin/plan_edit.html', 
        plan=plan, 
        current_user=current_user,
        title='Edit Subscription Plan'
    )


@admin_bp.route('/subscriptions/delete/<plan_id>', methods=['POST'])
@admin_required
def delete_plan(plan_id):
    """Delete subscription plan."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get subscription plan
    subscription_model = SubscriptionPlan()
    plan = subscription_model.get_plan_by_id(plan_id)
    
    if not plan:
        flash('Plan not found', 'danger')
        return redirect(url_for('admin.subscriptions'))
    
    # Check if plan has active users
    user_count = user_model.collection.count_documents({
        "subscription.planId": ObjectId(plan_id),
        "subscription.status": "active"
    })
    
    if user_count > 0:
        flash(f'Cannot delete plan: {user_count} active users are subscribed to this plan', 'danger')
        return redirect(url_for('admin.subscriptions'))
    
    # Delete plan
    success = subscription_model.delete_plan(plan_id)
    
    if success:
        flash('Subscription plan deleted successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' deleted subscription plan '{plan['name']}'")
    else:
        flash('Failed to delete plan', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to delete subscription plan '{plan['name']}'")
    
    return redirect(url_for('admin.subscriptions'))


@admin_bp.route('/transactions')
@admin_required
def transactions():
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


@admin_bp.route('/transactions/<transaction_id>')
@admin_required
def transaction_details(transaction_id):
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
        'subscription_end': user["subscription"].get("endDate") if user else None,
        'gateway_response': {
            'transaction_id': tx["paymentId"],
            'payer_id': 'PAYER123456',  # Demo data
            'payer_email': email,
            'payment_status': tx["status"].upper(),
            'payment_time': tx["createdAt"].strftime('%Y-%m-%dT%H:%M:%SZ'),
            'currency': 'USD',
            'fee': '1.17'  # Demo data
        }
    }
    
    # Render transaction details template
    return render_template(
        'admin/transaction_details.html', 
        transaction=transaction, 
        current_user=current_user,
        title='Transaction Details'
    )


@admin_bp.route('/transactions/update-status/<transaction_id>', methods=['POST'])
@admin_required
def update_transaction_status(transaction_id):
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


@admin_bp.route('/maintenance')
@admin_required
def maintenance():
    """System maintenance page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Mock maintenance info and system stats
    system_stats = {
        'uptime': '24d 12h 36m',
        'memory_usage': 62,
        'cpu_usage': 35,
        'disk_usage': 48,
        'active_connections': 18,
        'maintenance_mode': False,
        'maintenance_message': 'We are currently performing scheduled maintenance. Please check back later.',
        'last_backup': datetime.now() - timedelta(days=1),
    }
    
    # Get list of backups
    backups = [
        {
            'filename': 'backup_full_20250312_020000.tar.gz',
            'type': 'Full',
            'size': '24.5 MB',
            'created_at': datetime.now() - timedelta(days=1),
        },
        {
            'filename': 'backup_full_20250305_020000.tar.gz',
            'type': 'Full',
            'size': '23.8 MB',
            'created_at': datetime.now() - timedelta(days=8),
        }
    ]
    
    # Database stats
    db_stats = {
        'total_collections': 7,
        'total_documents': 15425,
        'total_size': '48.6 MB',
        'avg_document_size': '3.25 KB',
        'indexes': 18,
        'indexes_size': '12.8 MB'
    }
    
    # Get system logs related to backups and maintenance
    maintenance_logs = [
        {
            'timestamp': datetime.now() - timedelta(hours=24),
            'level': 'INFO',
            'action': 'Database backup',
            'details': 'Automatic daily backup completed successfully'
        },
        {
            'timestamp': datetime.now() - timedelta(days=3),
            'level': 'INFO',
            'action': 'Database backup',
            'details': 'Manual backup of users and transactions completed'
        },
        {
            'timestamp': datetime.now() - timedelta(days=8),
            'level': 'INFO',
            'action': 'Database backup',
            'details': 'Automatic daily backup completed successfully'
        },
        {
            'timestamp': datetime.now() - timedelta(days=10),
            'level': 'WARNING',
            'action': 'Maintenance',
            'details': 'Maintenance mode enabled for system updates'
        },
        {
            'timestamp': datetime.now() - timedelta(days=10, hours=2),
            'level': 'INFO',
            'action': 'Maintenance',
            'details': 'Maintenance mode disabled after successful updates'
        }
    ]
    
    # Render maintenance template
    return render_template(
        'admin/maintenance.html', 
        backups=backups,
        system_stats=system_stats,
        db_stats=db_stats,
        maintenance_logs=maintenance_logs,
        current_user=current_user,
        title='System Maintenance'
    )


@admin_bp.route('/update-maintenance', methods=['POST'])
@admin_required
def update_maintenance():
    """AJAX endpoint to update maintenance mode settings."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get request data
    data = request.get_json()
    enabled = data.get('enabled', False)
    message = data.get('message', '')
    duration = data.get('duration', 'indefinite')
    
    # In a real app, you would save these settings to database or config
    logger.info(f"Admin '{current_user['username']}' updated maintenance mode: enabled={enabled}")
    
    return jsonify({
        'success': True,
        'message': 'Maintenance settings updated successfully'
    })


@admin_bp.route('/generate-report', methods=['POST'])
@admin_required
def generate_report():
    """Generate various reports."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get form data
    report_type = request.form.get('report_type')
    date_range = request.form.get('date_range')
    report_format = request.form.get('report_format')
    
    # Generate report (mock implementation)
    logger.info(f"Admin '{current_user['username']}' generated {report_type} report in {report_format} format")
    
    # Flash success message and redirect
    flash(f'{report_type.capitalize()} report generated successfully in {report_format.upper()} format', 'success')
    return redirect(url_for('admin.dashboard'))

# These are the routes to be added to web/routes/admin.py

# Import necessary modules
from database.settings import Settings

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Admin settings page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Initialize settings model
    settings_model = Settings()
    
    # Handle form submissions
    if request.method == 'POST':
        # Determine which settings form was submitted
        form_type = request.form.get('form_type', '')
        active_tab = request.form.get('active_tab', 'general')
        
        if form_type == 'general':
            # Process general settings form
            settings_data = {
                'general.site_name': request.form.get('siteName'),
                'general.site_description': request.form.get('siteDescription'),
                'general.timezone': request.form.get('timezone'),
                'general.maintenance_mode': 'maintenanceMode' in request.form,
                'general.maintenance_message': request.form.get('maintenanceMessage', '')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['MAINTENANCE_MODE'] = 'maintenanceMode' in request.form
                current_app.config['MAINTENANCE_MESSAGE'] = request.form.get('maintenanceMessage', '')
                
                flash('General settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated general settings")
            else:
                flash('Failed to update general settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update general settings")
            
        elif form_type == 'email':
            # Process email settings form
            smtp_password = request.form.get('smtpPassword')
            
            # Don't update password if it's masked
            if smtp_password == '••••••••••••':
                smtp_password = settings_model.get_setting('email.smtp_password', '')
            
            settings_data = {
                'email.smtp_server': request.form.get('smtpServer'),
                'email.smtp_port': int(request.form.get('smtpPort', 587)),
                'email.smtp_security': request.form.get('smtpSecurity', 'starttls'),
                'email.smtp_username': request.form.get('smtpUsername'),
                'email.smtp_password': smtp_password,
                'email.sender_email': request.form.get('senderEmail'),
                'email.sender_name': request.form.get('senderName')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['SMTP_SERVER'] = request.form.get('smtpServer')
                current_app.config['SMTP_PORT'] = int(request.form.get('smtpPort', 587))
                current_app.config['SMTP_USERNAME'] = request.form.get('smtpUsername')
                current_app.config['SMTP_PASSWORD'] = smtp_password
                current_app.config['EMAIL_FROM'] = f"{request.form.get('senderName')} <{request.form.get('senderEmail')}>"
                
                flash('Email settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated email settings")
            else:
                flash('Failed to update email settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update email settings")
            
        elif form_type == 'payment':
            # Process payment settings form
            paypal_secret = request.form.get('paypalSecret')
            stripe_secret_key = request.form.get('stripeSecretKey')
            
            # Don't update secrets if they're masked
            if paypal_secret == '••••••••••••':
                paypal_secret = settings_model.get_setting('payment.paypal_secret', '')
                
            if stripe_secret_key == '••••••••••••':
                stripe_secret_key = settings_model.get_setting('payment.stripe_secret_key', '')
            
            settings_data = {
                'payment.paypal_enabled': 'paypalEnabled' in request.form,
                'payment.paypal_mode': request.form.get('paypalMode'),
                'payment.paypal_client_id': request.form.get('paypalClientId'),
                'payment.paypal_secret': paypal_secret,
                'payment.stripe_enabled': 'stripeEnabled' in request.form,
                'payment.stripe_mode': request.form.get('stripeMode'),
                'payment.stripe_publishable_key': request.form.get('stripePublishableKey'),
                'payment.stripe_secret_key': stripe_secret_key,
                'payment.currency': request.form.get('currency'),
                'payment.currency_position': request.form.get('currencyPosition')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['PAYPAL_CLIENT_ID'] = request.form.get('paypalClientId')
                current_app.config['PAYPAL_SECRET'] = paypal_secret
                current_app.config['PAYPAL_MODE'] = request.form.get('paypalMode')
                
                flash('Payment settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated payment settings")
            else:
                flash('Failed to update payment settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update payment settings")
            
        elif form_type == 'security':
            # Process security settings form
            settings_data = {
                'security.email_verification': 'emailVerification' in request.form,
                'security.session_timeout': int(request.form.get('sessionTimeout', 60)),
                'security.max_login_attempts': int(request.form.get('maxLoginAttempts', 5)),
                'security.account_lock_duration': int(request.form.get('accountLockDuration', 30)),
                'security.password_policy': request.form.get('passwordPolicy'),
                'security.password_expiry': int(request.form.get('passwordExpiry', 90)),
                'security.force_https': 'forceHttps' in request.form,
                'security.enable_hsts': 'enableHSTS' in request.form,
                'security.enable_csp': 'enableCSP' in request.form,
                'security.x_frame_options': request.form.get('xFrameOptions')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['SESSION_PERMANENT'] = True
                current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=int(request.form.get('sessionTimeout', 60)))
                
                flash('Security settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated security settings")
            else:
                flash('Failed to update security settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update security settings")
            
        elif form_type == 'backup':
            # Process backup settings form
            settings_data = {
                'backup.auto_backup': 'autoBackup' in request.form,
                'backup.backup_frequency': request.form.get('backupFrequency'),
                'backup.backup_time': request.form.get('backupTime'),
                'backup.backup_type': request.form.get('backupType'),
                'backup.compress_backups': 'compressBackups' in request.form,
                'backup.retention_period': int(request.form.get('retentionPeriod', 30)),
                'backup.max_backups': int(request.form.get('maxBackups', 10)),
                'backup.backup_location': request.form.get('backupLocation'),
                'backup.external_storage': 'externalStorage' in request.form,
                'backup.external_storage_type': request.form.get('externalStorageType')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['BACKUP_DIR'] = request.form.get('backupLocation')
                
                flash('Backup settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated backup settings")
            else:
                flash('Failed to update backup settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update backup settings")
        
        elif form_type == 'test_email':
            # Process test email form
            test_email = request.form.get('testEmailAddress')
            
            # In a real application, this would send an actual test email
            # from auth.mail import send_mail
            # success = send_mail(test_email, 'Test Email', 'This is a test email from Travian Whispers.')
            
            success = True  # For demonstration purposes
            
            if success:
                flash(f'Test email sent to {test_email}', 'success')
                logger.info(f"Admin '{current_user['username']}' sent a test email to {test_email}")
            else:
                flash(f'Failed to send test email to {test_email}', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to send a test email to {test_email}")
        
        # Redirect to maintain the active tab
        return redirect(url_for('admin.settings', tab=active_tab))
    
    # Mock settings data for the template
    # In a real application, this would be retrieved from the database
    settings = {
        'general': {
            'site_name': settings_model.get_setting('general.site_name', 'Travian Whispers'),
            'site_description': settings_model.get_setting('general.site_description', 'Advanced Travian Automation Suite'),
            'timezone': settings_model.get_setting('general.timezone', 'UTC'),
            'maintenance_mode': settings_model.get_setting('general.maintenance_mode', False),
            'maintenance_message': settings_model.get_setting('general.maintenance_message', 'We are currently performing scheduled maintenance. Please check back later.')
        },
        'email': {
            'smtp_server': settings_model.get_setting('email.smtp_server', 'smtp.gmail.com'),
            'smtp_port': settings_model.get_setting('email.smtp_port', 587),
            'smtp_username': settings_model.get_setting('email.smtp_username', 'your-email@gmail.com'),
            'smtp_password': '••••••••••••',  # Masked for security
            'sender_email': settings_model.get_setting('email.sender_email', 'noreply@travianwhispers.com'),
            'sender_name': settings_model.get_setting('email.sender_name', 'Travian Whispers')
        },
        'payment': {
            'paypal_mode': settings_model.get_setting('payment.paypal_mode', 'sandbox'),
            'paypal_client_id': settings_model.get_setting('payment.paypal_client_id', 'your-client-id'),
            'paypal_secret': '••••••••••••',  # Masked for security
            'paypal_enabled': settings_model.get_setting('payment.paypal_enabled', True),
            'stripe_enabled': settings_model.get_setting('payment.stripe_enabled', False),
            'currency': settings_model.get_setting('payment.currency', 'USD'),
            'currency_position': settings_model.get_setting('payment.currency_position', 'before')
        },
        'security': {
            'email_verification': settings_model.get_setting('security.email_verification', True),
            'session_timeout': settings_model.get_setting('security.session_timeout', 60),
            'max_login_attempts': settings_model.get_setting('security.max_login_attempts', 5),
            'account_lock_duration': settings_model.get_setting('security.account_lock_duration', 30),
            'password_policy': settings_model.get_setting('security.password_policy', 'standard'),
            'force_https': settings_model.get_setting('security.force_https', True),
            'enable_hsts': settings_model.get_setting('security.enable_hsts', True)
        },
        'backup': {
            'auto_backup': settings_model.get_setting('backup.auto_backup', True),
            'backup_frequency': settings_model.get_setting('backup.backup_frequency', 'weekly'),
            'retention_period': settings_model.get_setting('backup.retention_period', 30)
        },
        'system': {
            'version': '1.0.0',
            'environment': 'Production',
            'debug_mode': False,
            'uptime': '23 days, 4 hours',
            'php_version': '8.1.0',
            'python_version': '3.10.0',
            'server_software': 'nginx/1.21.4',
            'database': 'MongoDB 5.0.5'
        }
    }
    
    # Mock backups data for the template
    backups = [
        {
            'filename': 'backup_full_20250312_020000.tar.gz',
            'type': 'Full',
            'size': '24.5 MB',
            'created_at': datetime.now() - timedelta(days=1),
        },
        {
            'filename': 'backup_full_20250305_020000.tar.gz',
            'type': 'Full',
            'size': '23.8 MB',
            'created_at': datetime.now() - timedelta(days=8),
        },
        {
            'filename': 'backup_users_20250310_150000.tar.gz',
            'type': 'Users Only',
            'size': '8.2 MB',
            'created_at': datetime.now() - timedelta(days=3),
        }
    ]
    
    # Get system stats
    system_stats = {
        'cpu_usage': 35,
        'memory_usage': 62,
        'disk_usage': 48,
        'active_connections': 18
    }
    
    # Mock dependencies data
    dependencies = {
        'flask': '2.3.2',
        'pymongo': '4.5.0',
        'flask_wtf': '1.1.1',
        'passlib': '1.7.4',
        'psutil': '5.9.5'
    }
    
    # Render settings template with the data
    return render_template(
        'admin/settings.html', 
        settings=settings,
        backups=backups,
        system_stats=system_stats,
        dependencies=dependencies,
        current_user=current_user,
        title='System Settings'
    )


@admin_bp.route('/test-email', methods=['POST'])
@admin_required
def test_email():
    """Test email configuration."""
    # This is handled directly in the settings route
    return redirect(url_for('admin.settings', tab='email'))


@admin_bp.route('/backups')
@admin_required
def backups():
    """View all database backups."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get list of backups
    # This would use your backup model to retrieve all backups
    backups = []  # In a real app, you'd pull this from the database
    
    # Render backups template
    return render_template(
        'admin/backups.html', 
        backups=backups,
        current_user=current_user,
        title='Database Backups'
    )
    
@admin_bp.route('/create-backup', methods=['POST'])
@admin_required
def create_backup_route():
    """Create a database backup."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get form data
    backup_type = request.form.get('backup_type', 'full')
    compress_backup = 'compress_backup' in request.form
    
    # Create an actual backup
    from database.backup import create_backup
    success, backup_path = create_backup()
    
    if success and backup_path:
        filename = backup_path.name
        flash(f'Backup created successfully: {filename}', 'success')
        logger.info(f"Admin '{current_user['username']}' created backup: {filename}")
    else:
        flash('Failed to create backup', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to create backup")
    
    return redirect(url_for('admin.settings', tab='backup'))


@admin_bp.route('/restore-backup', methods=['POST'])
@admin_required
def restore_backup():
    """Restore a database backup."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get filename from form
    filename = request.form.get('filename')
    
    if not filename:
        flash('No backup file specified', 'danger')
        return redirect(url_for('admin.settings', tab='backup'))
    
    # In a real application, this would restore the backup
    # success = restore_backup_from_file(filename)
    success = True  # For demonstration purposes
    
    if success:
        flash(f'Backup {filename} restored successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' restored backup: {filename}")
    else:
        flash(f'Failed to restore backup {filename}', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to restore backup: {filename}")
    
    return redirect(url_for('admin.settings', tab='backup'))


@admin_bp.route('/delete-backup', methods=['POST'])
@admin_required
def delete_backup():
    """Delete a database backup."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get filename from form
    filename = request.form.get('filename')
    
    if not filename:
        flash('No backup file specified', 'danger')
        return redirect(url_for('admin.settings', tab='backup'))
    
    # In a real application, this would delete the backup file
    # success = delete_backup_file(filename)
    success = True  # For demonstration purposes
    
    if success:
        flash(f'Backup {filename} deleted successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' deleted backup: {filename}")
    else:
        flash(f'Failed to delete backup {filename}', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to delete backup: {filename}")
    
    return redirect(url_for('admin.settings', tab='backup'))


@admin_bp.route('/download-backup/<filename>')
@admin_required
def download_backup(filename):
    """Download a backup file."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # In a real application, this would serve the backup file for download
    # from flask import send_from_directory
    # return send_from_directory(current_app.config['BACKUP_DIR'], filename, as_attachment=True)
    
    # For demonstration purposes, redirect back to settings
    flash(f'Would download backup file: {filename}', 'info')
    logger.info(f"Admin '{current_user['username']}' downloaded backup: {filename}")
    
    return redirect(url_for('admin.settings', tab='backup'))

@admin_bp.route('/logs')
@admin_required
def logs():
    """System logs page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Mock log data
    logs = [
        {
            'id': 1,
            'timestamp': datetime.now() - timedelta(hours=1),
            'level': 'INFO',
            'user': 'admin',
            'action': 'System backup created',
            'ip_address': '192.168.1.1',
            'details': 'Full backup completed successfully'
        },
        {
            'id': 2,
            'timestamp': datetime.now() - timedelta(hours=2),
            'level': 'WARNING',
            'user': 'system',
            'action': 'High memory usage detected',
            'ip_address': '127.0.0.1',
            'details': 'Memory usage reached 85%'
        },
        {
            'id': 3,
            'timestamp': datetime.now() - timedelta(hours=3),
            'level': 'ERROR',
            'user': 'john_doe',
            'action': 'Failed login attempt',
            'ip_address': '192.168.1.2',
            'details': 'Multiple failed login attempts detected'
        },
        {
            'id': 4,
            'timestamp': datetime.now() - timedelta(hours=5),
            'level': 'INFO',
            'user': 'jane_smith',
            'action': 'Subscription upgraded',
            'ip_address': '192.168.1.3',
            'details': 'Upgraded from Basic to Premium plan'
        },
        {
            'id': 5,
            'timestamp': datetime.now() - timedelta(hours=8),
            'level': 'INFO',
            'user': 'admin',
            'action': 'User account created',
            'ip_address': '192.168.1.1',
            'details': 'Created new user: new_user'
        }
    ]
    
    # Filter logs based on query parameters
    log_level = request.args.get('level')
    user_filter = request.args.get('user')
    
    if log_level:
        logs = [log for log in logs if log['level'].lower() == log_level.lower()]
    
    if user_filter:
        logs = [log for log in logs if user_filter.lower() in log['user'].lower()]
    
    # Count logs by level
    info_count = sum(1 for log in logs if log['level'] == 'INFO')
    warning_count = sum(1 for log in logs if log['level'] == 'WARNING')
    error_count = sum(1 for log in logs if log['level'] == 'ERROR')
    
    # Create log stats dictionary
    log_stats = {
        'total': len(logs),
        'info': info_count,
        'warning': warning_count,
        'error': error_count
    }
    
    # Render logs template
    return render_template(
        'admin/logs.html',
        logs=logs,
        log_stats=log_stats,
        current_user=current_user,
        title='System Logs'
    )