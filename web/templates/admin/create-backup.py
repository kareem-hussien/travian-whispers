@admin_bp.route('/create-backup', methods=['POST'])
@admin_required
def create_backup_route():
    """AJAX endpoint to create database backup."""
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
    success, backup_path = create_backup(backup_type=backup_type, compress=compress_backup)
    
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
        })
