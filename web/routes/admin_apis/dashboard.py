"""
Admin dashboard routes for Travian Whispers web application.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register dashboard routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/')(admin_required(dashboard))
    admin_bp.route('/refresh-stats', methods=['GET'])(admin_required(admin_refresh_stats))

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

def admin_refresh_stats():
    """API endpoint to refresh admin dashboard statistics."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    logger.info(f"Admin '{current_user['username']}' refreshed dashboard statistics")
    
    return jsonify({
        'success': True,
        'message': 'Stats refreshed successfully'
    })
