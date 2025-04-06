"""
Admin maintenance routes for Travian Whispers web application.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import admin_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register maintenance routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/maintenance')(admin_required(maintenance))
    admin_bp.route('/update-maintenance', methods=['POST'])(admin_required(update_maintenance))
    admin_bp.route('/generate-report', methods=['POST'])(admin_required(generate_report))
    # Backup routes have been removed

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
        # Removed backup information
    }
    
    # Removed: Get list of backups
    
    # Database stats
    db_stats = {
        'total_collections': 7,
        'total_documents': 15425,
        'total_size': '48.6 MB',
        'avg_document_size': '3.25 KB',
        'indexes': 18,
        'indexes_size': '12.8 MB'
    }
    
    # Get system logs related to maintenance (backup logs removed)
    maintenance_logs = [
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
    
    # Render maintenance template (backup variable removed)
    return render_template(
        'admin/maintenance.html', 
        system_stats=system_stats,
        db_stats=db_stats,
        maintenance_logs=maintenance_logs,
        current_user=current_user,
        title='System Maintenance'
    )

def update_maintenance():
    """
    Update maintenance mode settings.
    Handles both form submissions and API requests.
    """
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get request data (supporting both JSON and form data)
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    enabled = data.get('enabled', False)
    message = data.get('message', '')
    duration = data.get('duration', 'indefinite')
    
    # In a real app, you would save these settings to database or config
    logger.info(f"Admin '{current_user['username']}' updated maintenance mode: enabled={enabled}")
    
    # Return based on request type
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Maintenance settings updated successfully'
        })
    else:
        flash('Maintenance settings updated successfully', 'success')
        return redirect(url_for('admin.maintenance'))

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
