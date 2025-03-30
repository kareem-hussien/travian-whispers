"""
Activity logs routes for Travian Whispers web application.
"""
import logging
from flask import (
    render_template, flash, session, redirect, url_for, request
)

from web.utils.decorators import login_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register activity logs routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/activity-logs')(login_required(activity_logs))

@login_required
def activity_logs():
    """Activity logs route."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        # Flash error message
        flash('User not found', 'danger')
        
        # Clear session and redirect to login
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get user activity logs from database
    from database.models.activity_log import ActivityLog
    activity_model = ActivityLog()
    
    # Get user activity logs with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Filter by activity type if specified
    activity_type = request.args.get('type')
    status = request.args.get('status')
    
    # Build filter
    filter_query = {"userId": session['user_id']}
    if activity_type:
        filter_query["activityType"] = activity_type
    if status:
        filter_query["status"] = status
    
    # Get paginated logs
    logs_data = activity_model.get_user_logs(
        user_id=session['user_id'],
        page=page,
        per_page=per_page,
        filter_query=filter_query
    )
    
    # Format activity logs for display
    activity_logs = []
    for log in logs_data.get('logs', []):
        activity_logs.append({
            'id': str(log.get('_id', '')),
            'timestamp': log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else 'N/A',
            'activity': log.get('activityType', 'Unknown').replace('-', ' ').title(),
            'details': log.get('details', 'No details'),
            'status': log.get('status', 'Unknown').title(),
            'village': log.get('village', 'N/A')
        })
    
    # Get activity statistics
    activity_stats = {
        'total': logs_data.get('total', 0),
        'auto_farm': activity_model.count_user_activities(user_id=session['user_id'], activity_type='auto-farm'),
        'training': activity_model.count_user_activities(user_id=session['user_id'], activity_type='troop-training'),
        'system': activity_model.count_user_activities(user_id=session['user_id'], activity_type='system'),
        'success': activity_model.count_user_activities(user_id=session['user_id'], status='success'),
        'warning': activity_model.count_user_activities(user_id=session['user_id'], status='warning'),
        'error': activity_model.count_user_activities(user_id=session['user_id'], status='error')
    }
    
    # Render activity logs template
    return render_template(
        'user/activity_logs.html', 
        logs=activity_logs,
        stats=activity_stats,
        current_user=user,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': logs_data.get('total', 0),
            'total_pages': logs_data.get('total_pages', 1)
        },
        filters={
            'type': activity_type,
            'status': status
        },
        title='Activity Logs'
    )
