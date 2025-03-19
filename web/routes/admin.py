"""
Admin routes for Travian Whispers web application.
This module defines the blueprint for admin panel routes.
"""
import logging
from datetime import datetime, timedelta
import os
import psutil
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from database.models.log import ActivityLog
from database.models.system import SystemStatus
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
    activity_log_model = ActivityLog()
    system_status_model = SystemStatus()
    
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
    
    # Determine monthly goal (from configuration or based on business rules)
    monthly_goal = current_app.config.get('MONTHLY_REVENUE_GOAL', 15000)
    
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
    }) if basic_plan else 0
    
    standard_count = user_model.collection.count_documents({
        "subscription.status": "active", 
        "subscription.planId": standard_plan["_id"] if standard_plan else None
    }) if standard_plan else 0
    
    premium_count = user_model.collection.count_documents({
        "subscription.status": "active", 
        "subscription.planId": premium_plan["_id"] if premium_plan else None
    }) if premium_plan else 0
    
    # System status from system model or live metrics
    system_status = system_status_model.get_current_status()
    if not system_status:
        # Fall back to real-time system metrics if no stored status is available
        process = psutil.Process(os.getpid())
        
        # Calculate uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
        
        # Calculate memory usage
        memory_info = process.memory_info()
        memory_usage = (memory_info.rss / psutil.virtual_memory().total) * 100
        
        system_stats = {
            "status": "Healthy",
            "uptime": uptime_str,
            "memory_usage": round(memory_usage, 1),
            "maintenance_mode": current_app.config.get('MAINTENANCE_MODE', False),
            "maintenance_message": current_app.config.get('MAINTENANCE_MESSAGE', 
                "We are currently performing scheduled maintenance. Please check back later.")
        }
    else:
        system_stats = system_status
    
    # Get recent activity logs
    recent_activity_cursor = activity_log_model.collection.find().sort("timestamp", -1).limit(5)
    recent_activity = []
    
    for log in recent_activity_cursor:
        # Format status class for UI
        status_class = "bg-secondary"
        if log.get("level") == "success":
            status_class = "bg-success"
        elif log.get("level") == "warning":
            status_class = "bg-warning"
        elif log.get("level") == "error":
            status_class = "bg-danger"
        elif log.get("level") == "info":
            status_class = "bg-info"
            
        # Format timestamp
        timestamp = log.get("timestamp", datetime.now())
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
        else:
            timestamp_str = str(timestamp)
            
        recent_activity.append({
            "timestamp": timestamp_str,
            "username": log.get("username", "system"),
            "action": log.get("action", "Unknown action"),
            "status": log.get("status", "Info"),
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
        plan = subscription_model.get_plan_by_id(tx["planId"]) if "planId" in tx else None
        plan_name = plan["name"] if plan else "Unknown Plan"
        
        # Get username
        user = user_model.get_user_by_id(tx["userId"]) if "userId" in tx else None
        username = user["username"] if user else "Unknown User"
        
        # Format status class
        status_class = "bg-secondary"
        if tx.get("status") == "completed":
            status_class = "bg-success"
        elif tx.get("status") == "pending":
            status_class = "bg-warning"
        elif tx.get("status") == "failed":
            status_class = "bg-danger"
        elif tx.get("status") == "refunded":
            status_class = "bg-info"
        
        # Format date
        created_at = tx.get("createdAt", datetime.now())
        if isinstance(created_at, datetime):
            date_str = created_at.strftime('%Y-%m-%d')
        else:
            date_str = str(created_at)
        
        recent_transactions.append({
            "id": tx["_id"],
            "username": username,
            "plan": plan_name,
            "amount": tx.get("amount", 0),
            "date": date_str,
            "status": tx.get("status", "Unknown").capitalize(),
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

# Additional routes remain the same, but with mock data replaced with real data sources
# ...

@admin_bp.route('/maintenance')
@admin_required
def maintenance():
    """System maintenance page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get system status from database or system metrics
    system_status_model = SystemStatus()
    system_status = system_status_model.get_current_status()
    
    if not system_status:
        # Fall back to real-time system metrics
        process = psutil.Process(os.getpid())
        
        # Calculate uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days, remainder = divmod(uptime.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
        
        # Calculate memory and CPU usage
        memory_info = process.memory_info()
        memory_usage = (memory_info.rss / psutil.virtual_memory().total) * 100
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Calculate disk usage
        disk_usage = psutil.disk_usage('/').percent
        
        system_stats = {
            'uptime': uptime_str,
            'memory_usage': round(memory_usage, 1),
            'cpu_usage': cpu_usage,
            'disk_usage': disk_usage,
            'active_connections': len(psutil.net_connections()),
            'maintenance_mode': current_app.config.get('MAINTENANCE_MODE', False),
            'maintenance_message': current_app.config.get('MAINTENANCE_MESSAGE', 
                "We are currently performing scheduled maintenance. Please check back later."),
        }
    else:
        system_stats = system_status
    
    # Get real backup information from backup records
    from database.models.backup import BackupRecord
    backup_model = BackupRecord()
    backups = backup_model.list_backups(limit=5)
    
    # Get actual database stats from MongoDB
    db = current_app.db.get_db()
    db_stats_raw = db.command("dbStats")
    
    db_stats = {
        'total_collections': db_stats_raw.get('collections', 0),
        'total_documents': db_stats_raw.get('objects', 0),
        'total_size': f"{db_stats_raw.get('dataSize', 0) / (1024 * 1024):.1f} MB",
        'avg_document_size': f"{db_stats_raw.get('avgObjSize', 0) / 1024:.2f} KB",
        'indexes': db_stats_raw.get('indexes', 0),
        'indexes_size': f"{db_stats_raw.get('indexSize', 0) / (1024 * 1024):.1f} MB"
    }
    
    # Get actual maintenance logs
    activity_log_model = ActivityLog()
    maintenance_logs_cursor = activity_log_model.collection.find(
        {"category": {"$in": ["backup", "maintenance"]}}
    ).sort("timestamp", -1).limit(5)
    
    maintenance_logs = []
    for log in maintenance_logs_cursor:
        maintenance_logs.append({
            'timestamp': log.get('timestamp', datetime.now()),
            'level': log.get('level', 'INFO').upper(),
            'action': log.get('action', 'Unknown'),
            'details': log.get('details', '')
        })
    
    # Update last backup time
    last_backup = None
    if backups:
        last_backup = backups[0].get('created_at')
    system_stats['last_backup'] = last_backup
    
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

@admin_bp.route('/logs')
@admin_required
def logs():
    """System logs page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get actual logs from database
    activity_log_model = ActivityLog()
    
    # Apply filters
    query = {}
    log_level = request.args.get('level')
    user_filter = request.args.get('user')
    
    if log_level:
        query['level'] = log_level.lower()
    
    if user_filter:
        query['username'] = {"$regex": user_filter, "$options": "i"}
    
    # Get logs with pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    
    logs_cursor = activity_log_model.collection.find(query).sort(
        "timestamp", -1
    ).skip(skip).limit(per_page)
    
    logs = []
    for log in logs_cursor:
        logs.append({
            'id': log.get('_id'),
            'timestamp': log.get('timestamp', datetime.now()),
            'level': log.get('level', 'INFO').upper(),
            'user': log.get('username', 'system'),
            'action': log.get('action', ''),
            'ip_address': log.get('ip_address', '127.0.0.1'),
            'details': log.get('details', '')
        })
    
    # Count total for pagination
    total_logs = activity_log_model.collection.count_documents(query)
    total_pages = (total_logs + per_page - 1) // per_page
    
    # Render logs template
    return render_template(
        'admin/logs.html', 
        logs=logs,
        current_page=page,
        total_pages=total_pages,
        total_logs=total_logs,
        current_user=current_user,
        title='System Logs'
    )
