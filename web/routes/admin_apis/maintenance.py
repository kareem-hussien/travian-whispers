"""
Admin maintenance and backup routes for Travian Whispers web application.
"""
import logging
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import admin_required
from database.models.user import User
from database.backup import create_backup

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register maintenance and backup routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/maintenance')(admin_required(maintenance))
    admin_bp.route('/update-maintenance', methods=['POST'])(admin_required(update_maintenance))
    admin_bp.route('/generate-report', methods=['POST'])(admin_required(generate_report))
    admin_bp.route('/create-backup', methods=['POST'])(admin_required(create_backup_route))
    admin_bp.route('/admin/create-backup', methods=['POST'])(admin_required(admin_create_backup))
    admin_bp.route('/admin/update-maintenance', methods=['POST'])(admin_required(admin_update_maintenance))
    admin_bp.route('/backups')(admin_required(backups))
    admin_bp.route('/restore-backup', methods=['POST'])(admin_required(restore_backup))
    admin_bp.route('/delete-backup', methods=['POST'])(admin_required(delete_backup))
    admin_bp.route('/download-backup/<filename>')(admin_required(download_backup))

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

def admin_create_backup():
    """API endpoint to create database backup."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get request data
    data = request.get_json()
    backup_type = data.get('backup_type', 'full')
    compress_backup = data.get('compress_backup', True)
    
    # Import database backup function
    from database.backup import create_backup
    
    # Create backup
    success, backup_path = create_backup()
    
    if success and backup_path:
        filename = backup_path.name
        logger.info(f"Admin '{current_user['username']}' created backup: {filename}")
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'Backup created successfully'
        })
    else:
        logger.warning(f"Admin '{current_user['username']}' failed to create backup")
        return jsonify({
            'success': False,
            'message': 'Failed to create backup'
        }), 500

def admin_update_maintenance():
    """API endpoint to update maintenance mode settings."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get request data
    data = request.get_json()
    enabled = data.get('enabled', False)
    message = data.get('message', '')
    duration = data.get('duration', 'indefinite')
    
    # In a real implementation, this would save the settings to the database
    logger.info(f"Admin '{current_user['username']}' updated maintenance mode: enabled={enabled}")
    
    return jsonify({
        'success': True,
        'message': 'Maintenance settings updated successfully'
    })

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
