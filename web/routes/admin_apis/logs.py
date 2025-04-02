"""
Admin logs routes for Travian Whispers web application.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.system_log import SystemLog

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register logs routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/logs')(admin_required(logs))
    admin_bp.route('/api/logs/<log_id>')(admin_required(get_log_details))
    admin_bp.route('/download-logs', methods=['POST'])(admin_required(download_logs))
    admin_bp.route('/clear-logs', methods=['POST'])(admin_required(clear_logs))

def logs():
    """System logs page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Initialize system log model
    system_log = SystemLog()
    
    # Get filter parameters
    log_level = request.args.get('level')
    user_filter = request.args.get('user')
    
    # Parse date range if provided
    date_from = None
    date_to = None
    
    if request.args.get('date_from'):
        try:
            date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('date_to'):
        try:
            date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
            # Set to end of day
            date_to = date_to.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Get logs with pagination and filtering
    logs_data = system_log.get_logs(
        page=page,
        per_page=per_page,
        level=log_level,
        user=user_filter,
        date_from=date_from,
        date_to=date_to
    )
    
    # Format logs for display
    formatted_logs = []
    for log in logs_data.get('logs', []):
        # Determine status class based on level
        status_class = 'bg-info'
        if log.get('level') == 'warning':
            status_class = 'bg-warning'
        elif log.get('level') == 'error':
            status_class = 'bg-danger'
        elif log.get('level') == 'debug':
            status_class = 'bg-secondary'
        
        formatted_logs.append({
            'id': str(log.get('_id', '')),
            'timestamp': log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else 'N/A',
            'level': log.get('level', 'info').upper(),
            'user': log.get('user', 'system'),
            'action': log.get('message', 'Unknown action'),
            'ip_address': log.get('ip_address', 'N/A'),
            'details': log.get('details', ''),
            'status_class': status_class
        })
    
    # Get log counts by level
    log_stats = system_log.count_logs_by_level()
    
    # Get chart data for the last 24 hours
    chart_data = system_log.get_logs_by_timespan(hours=24)
    
    # Prepare chart data for JavaScript
    chart_labels = []
    chart_info_data = []
    chart_warning_data = []
    chart_error_data = []
    
    for data_point in chart_data:
        # Format timestamp for display
        chart_labels.append(datetime.strptime(data_point['timestamp'], '%Y-%m-%d %H:00').strftime('%H:00'))
        chart_info_data.append(data_point['info'])
        chart_warning_data.append(data_point['warning'])
        chart_error_data.append(data_point['error'])
    
    # Render logs template
    return render_template(
        'admin/logs.html',
        logs=formatted_logs,
        log_stats=log_stats,
        current_user=current_user,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': logs_data.get('total', 0),
            'total_pages': logs_data.get('total_pages', 1)
        },
        filters={
            'level': log_level,
            'user': user_filter,
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        },
        chart_data={
            'labels': chart_labels,
            'info_data': chart_info_data,
            'warning_data': chart_warning_data,
            'error_data': chart_error_data
        },
        title='System Logs'
    )

def get_log_details(log_id):
    """API endpoint to get detailed log information."""
    system_log = SystemLog()
    log = system_log.get_log_by_id(log_id)
    
    if not log:
        return jsonify({
            'success': False,
            'message': 'Log entry not found'
        }), 404
    
    # Format log for response
    response_data = {
        'id': str(log.get('_id')),
        'timestamp': log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S'),
        'level': log.get('level', 'info').upper(),
        'user': log.get('user', 'system'),
        'message': log.get('message', ''),
        'details': log.get('details', ''),
        'ip_address': log.get('ip_address', 'N/A'),
        'category': log.get('category', 'General'),
        'stack_trace': log.get('stack_trace', '')
    }
    
    return jsonify({
        'success': True,
        'log': response_data
    })

def download_logs():
    """Download logs based on filter criteria."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get form data
    log_level = request.form.get('level', 'all')
    date_range = request.form.get('date_range', 'last7days')
    download_format = request.form.get('format', 'csv')
    
    # Apply date range filter
    date_from = None
    date_to = None
    
    if date_range == 'today':
        date_from = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'yesterday':
        date_from = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = date_from.replace(hour=23, minute=59, second=59)
    elif date_range == 'last7days':
        date_from = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'last30days':
        date_from = (datetime.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'thisMonth':
        date_from = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'lastMonth':
        last_month = datetime.now().month - 1
        last_month_year = datetime.now().year
        if last_month == 0:
            last_month = 12
            last_month_year -= 1
        date_from = datetime(last_month_year, last_month, 1, 0, 0, 0)
        if last_month == 12:
            date_to = datetime(last_month_year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            date_to = datetime(last_month_year, last_month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
    elif date_range == 'custom':
        if request.form.get('date_from'):
            date_from = datetime.strptime(request.form.get('date_from'), '%Y-%m-%d')
        if request.form.get('date_to'):
            date_to = datetime.strptime(request.form.get('date_to'), '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    # Initialize system log model
    system_log = SystemLog()
    
    # Get logs with filtering (no pagination for download)
    logs_query = {}
    
    if log_level != 'all':
        logs_query['level'] = log_level
    
    if date_from or date_to:
        logs_query['timestamp'] = {}
        if date_from:
            logs_query['timestamp']['$gte'] = date_from
        if date_to:
            logs_query['timestamp']['$lte'] = date_to
    
    # In a real implementation, we would query all logs matching criteria,
    # format them according to the requested format, and return a downloadable file
    
    # For demonstration purposes, we'll just log the request
    logger.info(f"Admin '{current_user['username']}' downloaded logs with filter: level={log_level}, range={date_range}, format={download_format}")
    
    # Flash message and redirect
    flash(f'Logs downloaded in {download_format.upper()} format', 'success')
    return redirect(url_for('admin.logs'))

def clear_logs():
    """Clear old logs from the system."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get form data
    retention_days = int(request.form.get('retention_days', 30))
    
    # Initialize system log model
    system_log = SystemLog()
    
    # Delete old logs
    deleted_count = system_log.delete_logs_older_than(retention_days)
    
    # Log the action
    logger.info(f"Admin '{current_user['username']}' cleared logs older than {retention_days} days. {deleted_count} logs deleted.")
    
    # Flash message and redirect
    flash(f'Successfully cleared {deleted_count} logs older than {retention_days} days', 'success')
    return redirect(url_for('admin.logs'))
