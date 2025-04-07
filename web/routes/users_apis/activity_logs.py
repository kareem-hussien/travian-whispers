"""
Activity logs routes for Travian Whispers web application.
"""
import logging
import csv
import io
import json
from datetime import datetime, timedelta
from flask import (
    render_template, flash, session, redirect, 
    url_for, request, jsonify, Response, current_app
)

from web.utils.decorators import login_required, api_error_handler
from database.models.user import User
from database.models.activity_log import ActivityLog

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(user_bp):
    """Register activity logs routes with the user blueprint."""
    # Attach routes to the blueprint
    user_bp.route('/activity-logs')(login_required(activity_logs))
    user_bp.route('/api/user/activity-logs/export')(login_required(export_activity_logs))

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
    
    # Get filter parameters
    activity_type = request.args.get('type')
    status = request.args.get('status')
    village = request.args.get('village')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Build filter query
    filter_query = {"userId": session['user_id']}
    if activity_type:
        filter_query["activityType"] = activity_type
    if status:
        filter_query["status"] = status
    if village:
        filter_query["village"] = village
    
    # Get activity logs from database
    activity_model = ActivityLog()
    
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
            'activity': log.get('activityType', 'Unknown'),
            'details': log.get('details', 'No details'),
            'status': log.get('status', 'Unknown'),
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
            'status': status,
            'village': village
        },
        title='Activity Logs'
    )

@login_required
@api_error_handler
def export_activity_logs():
    """API endpoint to export activity logs."""
    # Get export parameters
    export_format = request.args.get('format', 'csv')
    date_range = request.args.get('dateRange', 'all')
    include_filters = request.args.get('includeFilters', 'true').lower() == 'true'
    
    # Get filter parameters if including filters
    activity_type = request.args.get('type') if include_filters else None
    status = request.args.get('status') if include_filters else None
    village = request.args.get('village') if include_filters else None
    
    # Get custom date range if selected
    start_date = None
    end_date = None
    
    if date_range == 'custom':
        try:
            start_date_str = request.args.get('startDate')
            end_date_str = request.args.get('endDate')
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                # Set end date to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing date range: {e}")
    elif date_range == 'today':
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now()
    elif date_range == 'week':
        today = datetime.now()
        start_date = today - timedelta(days=today.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now()
    elif date_range == 'month':
        today = datetime.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now()
    
    # Build filter query
    filter_query = {"userId": session['user_id']}
    if activity_type:
        filter_query["activityType"] = activity_type
    if status:
        filter_query["status"] = status
    if village:
        filter_query["village"] = village
    
    # Add date range to filter query
    if start_date or end_date:
        filter_query["timestamp"] = {}
        if start_date:
            filter_query["timestamp"]["$gte"] = start_date
        if end_date:
            filter_query["timestamp"]["$lte"] = end_date
    
    # Get activity logs from database
    activity_model = ActivityLog()
    
    # Get all logs that match the filter (no pagination)
    all_logs = list(activity_model.collection.find(filter_query).sort("timestamp", -1))
    
    # Format logs for export
    formatted_logs = []
    for log in all_logs:
        formatted_logs.append({
            'timestamp': log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else 'N/A',
            'activity_type': log.get('activityType', 'Unknown'),
            'details': log.get('details', 'No details'),
            'status': log.get('status', 'Unknown'),
            'village': log.get('village', 'N/A'),
            'data': log.get('data', {})
        })
    
    # Export as CSV or JSON
    if export_format == 'csv':
        return export_as_csv(formatted_logs)
    else:
        return export_as_json(formatted_logs)

def export_as_csv(logs):
    """
    Export logs as CSV file.
    
    Args:
        logs (list): List of log dictionaries
        
    Returns:
        Response: Flask response with CSV file
    """
    # Create CSV file in memory
    output = io.StringIO()
    fieldnames = ['timestamp', 'activity_type', 'details', 'status', 'village']
    
    # Create CSV writer
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    
    # Write logs
    for log in logs:
        # Only include the specified fields
        row = {field: log.get(field, '') for field in fieldnames}
        writer.writerow(row)
    
    # Create response
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )
    
    return response

def export_as_json(logs):
    """
    Export logs as JSON file.
    
    Args:
        logs (list): List of log dictionaries
        
    Returns:
        Response: Flask response with JSON file
    """
    # Convert ObjectId and datetime objects to strings
    for log in logs:
        for key, value in log.items():
            if isinstance(value, datetime):
                log[key] = value.strftime('%Y-%m-%d %H:%M:%S')
    
    # Create response
    response = Response(
        json.dumps(logs, indent=2),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        }
    )
    
    return response