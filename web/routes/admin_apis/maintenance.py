"""
Maintenance routes for Travian Whispers admin panel.
This module defines the maintenance and system log routes for the admin panel.
"""
import logging
import os
import psutil
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, current_app, jsonify

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.log import ActivityLog
from database.models.system import SystemStatus
from database.models.backup import BackupRecord
from database.backup import create_backup

# Initialize logger
logger = logging.getLogger(__name__)

@admin_required
def index():
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

@admin_required
def create_backup():
    """API endpoint to create a database backup."""
    # Get current user
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get backup parameters
    backup_type = request.json.get('backup_type', 'full')
    compress_backup = request.json.get('compress_backup', True)
    
    # Create backup
    try:
        backup_result = create_backup(backup_type, compress_backup)
        
        if backup_result and 'success' in backup_result and backup_result['success']:
            # Log backup creation
            logger.info(f"Admin '{current_user['username']}' created {backup_type} backup")
            
            return jsonify({
                'success': True,
                'filename': backup_result.get('filename', 'backup.json'),
                'message': f"{backup_type.capitalize()} backup created successfully"
            })
        else:
            error_msg = backup_result.get('error', 'Unknown error') if backup_result else 'Failed to create backup'
            logger.error(f"Admin '{current_user['username']}' failed to create backup: {error_msg}")
            
            return jsonify({
                'success': False,
                'message': error_msg
            })
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error creating backup: {str(e)}"
        })

@admin_required
def restore_backup():
    """API endpoint to restore a database backup."""
    # Get current user
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get backup filename
    filename = request.json.get('filename')
    
    if not filename:
        return jsonify({
            'success': False,
            'message': 'No backup file specified'
        })
    
    # Restore backup
    try:
        # Import restore function
        from database.backup import restore_backup
        
        restore_result = restore_backup(filename)
        
        if restore_result and 'success' in restore_result and restore_result['success']:
            # Log backup restoration
            logger.info(f"Admin '{current_user['username']}' restored backup: {filename}")
            
            return jsonify({
                'success': True,
                'message': f"Backup restored successfully: {filename}"
            })
        else:
            error_msg = restore_result.get('error', 'Unknown error') if restore_result else 'Failed to restore backup'
            logger.error(f"Admin '{current_user['username']}' failed to restore backup: {error_msg}")
            
            return jsonify({
                'success': False,
                'message': error_msg
            })
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error restoring backup: {str(e)}"
        })

@admin_required
def update_maintenance():
    """API endpoint to update maintenance mode."""
    # Get current user
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get maintenance parameters
    enabled = request.json.get('enabled', False)
    message = request.json.get('message')
    duration = request.json.get('duration', 'indefinite')
    
    # Update maintenance mode
    try:
        system_status_model = SystemStatus()
        result = system_status_model.set_maintenance_mode(enabled, message)
        
        if result:
            # Log maintenance mode change
            action = "enabled" if enabled else "disabled"
            logger.info(f"Admin '{current_user['username']}' {action} maintenance mode")
            
            return jsonify({
                'success': True,
                'message': f"Maintenance mode {action} successfully"
            })
        else:
            logger.error(f"Admin '{current_user['username']}' failed to update maintenance mode")
            
            return jsonify({
                'success': False,
                'message': "Failed to update maintenance mode"
            })
    except Exception as e:
        logger.error(f"Error updating maintenance mode: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error updating maintenance mode: {str(e)}"
        })