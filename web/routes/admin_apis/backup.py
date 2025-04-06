"""
Admin backup management routes for Travian Whispers web application.
This module provides routes for database backup and restore operations.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from flask import (
    render_template, request, redirect, send_file,
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import admin_required
from database.models.user import User
from database.backup import create_backup, BackupError
from database.models.backup import BackupRecord

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register backup routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/create-backup', methods=['POST'], endpoint='create_backup')(admin_required(create_backup_route))
    admin_bp.route('/download-backup/<filename>')(admin_required(download_backup))
    admin_bp.route('/delete-backup', methods=['POST'])(admin_required(delete_backup))
    admin_bp.route('/restore-backup', methods=['POST'])(admin_required(restore_backup))
    admin_bp.route('/api/backups', methods=['GET'])(admin_required(get_backups))

def create_backup_route():
    """
    Create a database backup.
    Handles both form submissions and API requests.
    """
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get request data (supporting both JSON and form data)
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    backup_type = data.get('backup_type', 'full')
    compress_backup = data.get('compress_backup', True)
    
    # Check if backup type is valid
    valid_types = ['full', 'users', 'transactions', 'subscriptions']
    if backup_type not in valid_types:
        if request.is_json:
            return jsonify({
                'success': False,
                'message': f'Invalid backup type. Valid types are: {", ".join(valid_types)}'
            }), 400
        else:
            flash(f'Invalid backup type. Valid types are: {", ".join(valid_types)}', 'danger')
            return redirect(url_for('admin.settings', tab='backup'))
    
    try:
        # Create backup
        success, backup_path = create_backup(
            backup_type=backup_type,
            compress=compress_backup,
            connection_string=current_app.config.get('MONGODB_URI'),
            db_name=current_app.config.get('MONGODB_DB_NAME')
        )
        
        if success and backup_path:
            # Get file size
            file_size = os.path.getsize(backup_path)
            
            # Record backup in database
            backup_record = BackupRecord()
            backup_record.add_backup_record(
                filename=os.path.basename(backup_path),
                backup_type=backup_type,
                file_size=file_size,
                success=True,
                details=f"Created by admin user: {current_user['username']}"
            )
            
            logger.info(f"Admin '{current_user['username']}' created {backup_type} backup: {backup_path}")
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Backup created successfully',
                    'data': {
                        'filename': os.path.basename(backup_path),
                        'path': str(backup_path),
                        'size': file_size,
                        'type': backup_type
                    }
                })
            else:
                flash(f'{backup_type.capitalize()} backup created successfully', 'success')
                return redirect(url_for('admin.settings', tab='backup'))
        else:
            error_message = 'Failed to create backup'
            logger.error(f"Backup creation failed for admin '{current_user['username']}'")
            
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': error_message
                }), 500
            else:
                flash(error_message, 'danger')
                return redirect(url_for('admin.settings', tab='backup'))
    
    except BackupError as e:
        error_message = f"Backup error: {str(e)}"
        logger.error(error_message)
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': error_message
            }), 500
        else:
            flash(error_message, 'danger')
            return redirect(url_for('admin.settings', tab='backup'))
    
    except Exception as e:
        error_message = f"Unexpected error during backup: {str(e)}"
        logger.error(error_message)
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': error_message
            }), 500
        else:
            flash(error_message, 'danger')
            return redirect(url_for('admin.settings', tab='backup'))

def download_backup(filename):
    """
    Download a backup file.
    """
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename:
        flash('Invalid backup filename', 'danger')
        return redirect(url_for('admin.settings', tab='backup'))
    
    # Get backup directory from config or use default
    backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    # Check if file exists
    if not os.path.exists(backup_path):
        flash('Backup file not found', 'danger')
        return redirect(url_for('admin.settings', tab='backup'))
    
    logger.info(f"Admin '{current_user['username']}' downloaded backup: {filename}")
    
    # Return file for download
    return send_file(
        backup_path,
        as_attachment=True,
        download_name=filename
    )

def delete_backup():
    """
    Delete a backup file.
    Handles both form submissions and API requests.
    """
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get request data (supporting both JSON and form data)
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    filename = data.get('filename')
    record_id = data.get('record_id')
    
    if not filename and not record_id:
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Filename or record ID is required'
            }), 400
        else:
            flash('Filename or record ID is required', 'danger')
            return redirect(url_for('admin.settings', tab='backup'))
    
    # If record ID is provided, get filename from record
    backup_record = BackupRecord()
    if record_id:
        record = backup_record.get_backup_record(record_id)
        if record:
            filename = record.get('filename')
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Backup record not found'
                }), 404
            else:
                flash('Backup record not found', 'danger')
                return redirect(url_for('admin.settings', tab='backup'))
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename:
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Invalid backup filename'
            }), 400
        else:
            flash('Invalid backup filename', 'danger')
            return redirect(url_for('admin.settings', tab='backup'))
    
    # Get backup directory from config or use default
    backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    # Check if file exists
    if not os.path.exists(backup_path):
        # If record exists but file doesn't, delete the record
        if record_id:
            record_deleted = backup_record.delete_record(record_id)
            if record_deleted:
                logger.info(f"Admin '{current_user['username']}' deleted backup record for missing file: {filename}")
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': 'Backup record deleted (file was missing)'
                    })
                else:
                    flash('Backup record deleted (file was missing)', 'warning')
                    return redirect(url_for('admin.settings', tab='backup'))
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Backup file not found'
            }), 404
        else:
            flash('Backup file not found', 'danger')
            return redirect(url_for('admin.settings', tab='backup'))
    
    try:
        # Delete file
        os.remove(backup_path)
        logger.info(f"Admin '{current_user['username']}' deleted backup: {filename}")
        
        # Delete record if it exists
        if record_id:
            backup_record.delete_record(record_id)
        else:
            # Try to find and delete record by filename
            record = backup_record.get_backup_by_filename(filename)
            if record:
                backup_record.delete_record(str(record['_id']))
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Backup deleted successfully'
            })
        else:
            flash('Backup deleted successfully', 'success')
            return redirect(url_for('admin.settings', tab='backup'))
        
    except Exception as e:
        error_message = f"Error deleting backup: {str(e)}"
        logger.error(error_message)
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': error_message
            }), 500
        else:
            flash(error_message, 'danger')
            return redirect(url_for('admin.settings', tab='backup'))

def restore_backup():
    """
    Restore a database from a backup.
    Currently just a placeholder as this would be complex to implement.
    """
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get backup filename
    filename = request.form.get('filename')
    
    if not filename:
        flash('Backup filename is required', 'danger')
        return redirect(url_for('admin.settings', tab='backup'))
    
    # Log the attempt
    logger.info(f"Admin '{current_user['username']}' attempted to restore backup: {filename}")
    
    # This would be a complex operation requiring:
    # 1. Database connection handling
    # 2. Proper error recovery
    # 3. Data validation
    # 4. Progress reporting
    
    # For now, just show a message
    flash('Database restore functionality is not yet implemented', 'warning')
    return redirect(url_for('admin.settings', tab='backup'))

def get_backups():
    """
    API endpoint to get list of backups.
    """
    # Initialize backup record model
    backup_record = BackupRecord()
    
    # Get backups with additional details
    limit = request.args.get('limit', 20, type=int)
    backup_type = request.args.get('type')
    
    backups = backup_record.list_backups(limit=limit, backup_type=backup_type)
    
    # Format backups for response
    formatted_backups = []
    for backup in backups:
        formatted_backup = {
            'id': str(backup.get('_id')),
            'filename': backup.get('filename'),
            'type': backup.get('type'),
            'size': backup.get('size'),
            'created_at': backup.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if backup.get('created_at') else None,
            'success': backup.get('success', True),
            'details': backup.get('details')
        }
        formatted_backups.append(formatted_backup)
    
    return jsonify({
        'success': True,
        'data': formatted_backups
    })
