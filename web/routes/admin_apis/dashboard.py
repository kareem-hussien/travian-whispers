"""
Admin dashboard routes for Travian Whispers web application.
This module defines the dashboard route for the admin panel.
"""
import logging
from datetime import datetime, timedelta
from flask import render_template, session
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from database.models.log import SystemLog
from database.models.system import SystemStats

# Initialize logger
logger = logging.getLogger(__name__)

@admin_required
def index():
    """Admin dashboard route."""
    # Initialize models
    user_model = User()
    subscription_model = SubscriptionPlan()
    transaction_model = Transaction()
    system_log_model = SystemLog()
    
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
    
    # Get system stats
    system_stats_model = SystemStats()
    system_stats = system_stats_model.get_current_stats()
    
    # Get recent activity logs from the database
    recent_activity_cursor = system_log_model.get_recent_logs(limit=5)
    recent_activity = []
    
    for log in recent_activity_cursor:
        status_class = "bg-success"
        if log.get("level") == "warning":
            status_class = "bg-warning"
        elif log.get("level") == "error":
            status_class = "bg-danger"
            
        recent_activity.append({
            "timestamp": log.get("timestamp").strftime('%Y-%m-%d %H:%M'),
            "username": log.get("username"),
            "action": log.get("action"),
            "status": log.get("status"),
            "status_class": status_class
        })
    
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