"""
IP management routes for Travian Whispers web application.
This module defines the blueprint for IP management routes.
"""
import logging
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)

from web.utils.decorators import login_required, admin_required
from startup.ip_manager import IPManager
from startup.session_isolation import BrowserIsolationManager

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
ip_bp = Blueprint('ip', __name__, url_prefix='/dashboard/ip')

# Initialize managers
ip_manager = IPManager()
browser_manager = BrowserIsolationManager()

@ip_bp.route('/status')
@login_required
def ip_status():
    """
    Display IP status for the current user.
    """
    user_id = session.get('user_id')
    
    # Get IP assignment for user
    ip_assignment = ip_manager.ip_assignments.find_one({"userId": user_id})
    
    # Get IP data if assignment exists
    ip_data = None
    if ip_assignment:
        from bson.objectid import ObjectId
        ip_data = ip_manager.ip_collection.find_one({"_id": ObjectId(ip_assignment["ipId"])})
    
    # Prepare data for template
    ip_status = {
        "assigned": ip_assignment is not None,
        "ip": ip_data.get("ip") if ip_data else None,
        "status": ip_data.get("status") if ip_data else "unassigned",
        "last_used": ip_data.get("lastUsed") if ip_data else None,
        "last_rotated": ip_data.get("lastRotated") if ip_data else None,
        "error_count": ip_data.get("errorCount", 0) if ip_data else 0,
        "assignment_date": ip_assignment.get("assignedAt") if ip_assignment else None
    }
    
    # Render template
    return render_template(
        'user/ip_status.html',
        ip_status=ip_status,
        title='IP Status'
    )

@ip_bp.route('/rotate', methods=['POST'])
@login_required
def rotate_ip():
    """
    Rotate IP for the current user.
    """
    user_id = session.get('user_id')
    
    # Rotate IP
    new_ip = ip_manager.rotate_ip_for_user(user_id)
    
    if new_ip:
        flash('IP rotated successfully', 'success')
        logger.info(f"User {user_id} rotated IP to {new_ip['ip']}")
    else:
        flash('Failed to rotate IP', 'danger')
        logger.warning(f"Failed to rotate IP for user {user_id}")
    
    # Redirect back to IP status
    return redirect(url_for('ip.ip_status'))

@ip_bp.route('/rotate_identity', methods=['POST'])
@login_required
def rotate_identity():
    """
    Rotate entire digital identity (IP and browser session) for the current user.
    """
    user_id = session.get('user_id')
    
    # Rotate identity
    new_config = browser_manager.rotate_user_identity(user_id)
    
    if new_config:
        flash('Identity rotated successfully', 'success')
        logger.info(f"User {user_id} rotated digital identity")
    else:
        flash('Failed to rotate identity', 'danger')
        logger.warning(f"Failed to rotate identity for user {user_id}")
    
    # Redirect back to IP status
    return redirect(url_for('ip.ip_status'))

@ip_bp.route('/session_info')
@login_required
def session_info():
    """
    Display session information for the current user.
    """
    user_id = session.get('user_id')
    
    # Get session path
    session_path = browser_manager.session_manager.get_session_for_user(user_id, create=False)
    
    # Get active session info
    session_info = browser_manager.session_manager.active_sessions.get(user_id, {})
    
    # Prepare data for template
    browser_session = {
        "exists": session_path is not None,
        "path": session_path,
        "id": session_info.get("id"),
        "created_at": session_info.get("created_at")
    }
    
    # Render template
    return render_template(
        'user/session_info.html',
        browser_session=browser_session,
        title='Browser Session Info'
    )

@ip_bp.route('/clear_session', methods=['POST'])
@login_required
def clear_session():
    """
    Clear browser session for the current user.
    """
    user_id = session.get('user_id')
    
    # Clear session
    success = browser_manager.session_manager.clear_user_session(user_id)
    
    if success:
        flash('Browser session cleared successfully', 'success')
        logger.info(f"User {user_id} cleared browser session")
    else:
        flash('Failed to clear browser session', 'danger')
        logger.warning(f"Failed to clear browser session for user {user_id}")
    
    # Redirect back to session info
    return redirect(url_for('ip.session_info'))

# Admin-only routes for IP management
@ip_bp.route('/admin/ips')
@login_required
@admin_required
def admin_ips():
    """
    Admin IP management page.
    """
    # Get all IPs
    all_ips = list(ip_manager.ip_collection.find())
    
    # Get all assignments
    all_assignments = list(ip_manager.ip_assignments.find())
    
    # Render template
    return render_template(
        'admin/ip_management.html',
        ips=all_ips,
        assignments=all_assignments,
        title='IP Management'
    )

@ip_bp.route('/admin/add_ip', methods=['POST'])
@login_required
@admin_required
def admin_add_ip():
    """
    Add a new IP to the pool.
    """
    # Get form data
    ip = request.form.get('ip')
    port = request.form.get('port')
    username = request.form.get('username')
    password = request.form.get('password')
    proxy_type = request.form.get('proxy_type', 'http')
    
    # Add IP
    result = ip_manager.add_ip(ip, port, username, password, proxy_type)
    
    if result:
        flash('IP added successfully', 'success')
        logger.info(f"Admin added new IP {ip}")
    else:
        flash('Failed to add IP', 'danger')
        logger.warning(f"Admin failed to add IP {ip}")
    
    # Redirect back to IP management
    return redirect(url_for('ip.admin_ips'))

@ip_bp.route('/admin/remove_ip/<ip_id>', methods=['POST'])
@login_required
@admin_required
def admin_remove_ip(ip_id):
    """
    Remove an IP from the pool.
    """
    # Remove IP
    result = ip_manager.remove_ip(ip_id)
    
    if result:
        flash('IP removed successfully', 'success')
        logger.info(f"Admin removed IP {ip_id}")
    else:
        flash('Failed to remove IP', 'danger')
        logger.warning(f"Admin failed to remove IP {ip_id}")
    
    # Redirect back to IP management
    return redirect(url_for('ip.admin_ips'))

@ip_bp.route('/admin/rotate_all', methods=['POST'])
@login_required
@admin_required
def admin_rotate_all():
    """
    Rotate all IPs that have been used for too long.
    """
    # Get max age from form
    max_age_hours = int(request.form.get('max_age_hours', 24))
    
    # Schedule rotation
    rotated_count = ip_manager.schedule_ip_rotation(max_age_hours)
    
    flash(f'Rotated {rotated_count} IPs', 'success')
    logger.info(f"Admin rotated {rotated_count} IPs")
    
    # Redirect back to IP management
    return redirect(url_for('ip.admin_ips'))
