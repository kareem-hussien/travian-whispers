"""
User management routes for Travian Whispers admin panel.
This module defines the user management routes for the admin panel.
"""
import logging
from flask import render_template, request, redirect, url_for, flash, session
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

@admin_required
def index():
    """User management page."""
    # Initialize user model
    user_model = User()
    
    # Fetch all users from database
    users_cursor = user_model.collection.find()
    users = []
    
    for user in users_cursor:
        # Get subscription info
        subscription_status = user["subscription"]["status"]
        plan_id = user["subscription"].get("planId")
        
        subscription_plan = "None"
        if plan_id:
            from database.models.subscription import SubscriptionPlan
            plan_model = SubscriptionPlan()
            plan = plan_model.get_plan_by_id(plan_id)
            if plan:
                subscription_plan = plan["name"]
        
        # Format for template
        users.append({
            'id': user["_id"],
            'username': user["username"],
            'email': user["email"],
            'role': user["role"],
            'status': "active" if user.get("isVerified", False) else "inactive",
            'subscription': subscription_plan,
            'joined': user["createdAt"].strftime('%Y-%m-%d'),
            'verified': user.get("isVerified", False),
            'last_login': user.get("lastLoginAt", "Never")
        })
    
    # Filter users based on query parameters
    status_filter = request.args.get('status')
    role_filter = request.args.get('role')
    search_query = request.args.get('q')
    
    filtered_users = users
    
    if status_filter:
        filtered_users = [user for user in filtered_users if user['status'] == status_filter]
    
    if role_filter:
        filtered_users = [user for user in filtered_users if user['role'] == role_filter]
    
    if search_query:
        filtered_users = [
            user for user in filtered_users 
            if search_query.lower() in user['username'].lower() or search_query.lower() in user['email'].lower()
        ]
    
    # Get current user for the template
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Render user management template
    return render_template(
        'admin/users.html', 
        users=filtered_users, 
        current_user=current_user,
        title='User Management'
    )

@admin_required
def create():
    """Create user page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        # Process form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template(
                'admin/user_create.html', 
                current_user=current_user,
                title='Create User'
            )
        
        # Create user
        user_model = User()
        user = user_model.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            verification_token=None  # Admin-created users don't need verification
        )
        
        if user:
            # Mark as verified since admin is creating
            user_model.verify_user_by_id(str(user["_id"]))
            flash('User created successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' created user '{username}'")
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to create user. Username or email may already exist.', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to create user '{username}'")
    
    # Render user create template
    return render_template(
        'admin/user_create.html', 
        current_user=current_user,
        title='Create User'
    )

@admin_required
def edit(user_id):
    """Edit user page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get user to edit
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        # Process form data
        email = request.form.get('email')
        role = request.form.get('role')
        status = request.form.get('status')
        
        # Prepare update data
        update_data = {
            'email': email,
            'role': role,
            'isVerified': status == 'active'
        }
        
        # Process password change if provided
        new_password = request.form.get('new_password')
        
        # Update user
        success = user_model.update_user(user_id, update_data)

        if success:
            # Handle password change separately if needed
            if new_password:
                if not user_model.admin_reset_password(user_id, new_password):
                    flash('Failed to update password', 'warning')
                    logger.warning(f"Admin '{current_user['username']}' failed to update password for user '{user['username']}'")
            
            flash('User updated successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' updated user '{user['username']}'")
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to update user', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to update user '{user['username']}'")
    
    # Format for template
    formatted_user = {
        'id': user["_id"],
        'username': user["username"],
        'email': user["email"],
        'role': user["role"],
        'status': "active" if user.get("isVerified", False) else "inactive",
        'joined': user["createdAt"].strftime('%Y-%m-%d'),
        'last_login': user.get("lastLoginAt", "Never")
    }
    
    # Render user edit template
    return render_template(
        'admin/user_edit.html', 
        user=formatted_user, 
        current_user=current_user,
        title='Edit User'
    )

@admin_required
def delete(user_id):
    """Delete user."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get user to delete
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent self-deletion
    if str(user["_id"]) == session['user_id']:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    # Delete user
    success = user_model.delete_user(user_id)
    
    if success:
        flash('User deleted successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' deleted user '{user['username']}'")
    else:
        flash('Failed to delete user', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to delete user '{user['username']}'")
    
    return redirect(url_for('admin.users'))