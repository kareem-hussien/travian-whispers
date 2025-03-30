"""
Admin user management routes for Travian Whispers web application.
"""
import logging
import uuid
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app, jsonify
)
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.subscription import SubscriptionPlan

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register user management routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/users')(admin_required(users))
    admin_bp.route('/users/create', methods=['GET', 'POST'])(admin_required(user_create))
    admin_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])(admin_required(user_edit))
    admin_bp.route('/users/delete/<user_id>', methods=['POST'])(admin_required(user_delete))
    admin_bp.route('/user/<user_id>', methods=['GET'])(admin_required(admin_get_user))

def users():
    """User management page."""
    # Initialize user model
    user_model = User()
    
    # Get filter parameters
    status_filter = request.args.get('status')
    role_filter = request.args.get('role')
    search_query = request.args.get('q')
    sort_param = request.args.get('sort', '-joined')  # Default sort by newest first
    
    # Build query filter
    query_filter = {}
    
    if status_filter:
        if status_filter == 'active':
            query_filter["isVerified"] = True
        elif status_filter == 'inactive':
            query_filter["isVerified"] = False
    
    if role_filter:
        query_filter["role"] = role_filter
    
    if search_query:
        # Add search filter for username or email
        query_filter["$or"] = [
            {"username": {"$regex": search_query, "$options": "i"}},
            {"email": {"$regex": search_query, "$options": "i"}}
        ]
    
    # Determine sort field and direction
    sort_field = "createdAt"
    sort_direction = -1  # Default to descending (newest first)
    
    if sort_param:
        if sort_param.startswith('-'):
            sort_field = sort_param[1:]
            sort_direction = -1
        else:
            sort_field = sort_param
            sort_direction = 1
            
        # Map display field names to actual DB field names
        if sort_field == 'joined':
            sort_field = 'createdAt'
    
    # Fetch users from database with pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Use the paginate_query helper from database/models/init.py if available
    # Otherwise implement manual pagination
    try:
        from database.models.init import paginate_query
        users_cursor, total, page, per_page, total_pages = paginate_query(
            user_model.collection, 
            query_filter, 
            page=page, 
            per_page=per_page, 
            sort_by=sort_field, 
            sort_direction=sort_direction
        )
        users = list(users_cursor)
    except ImportError:
        # Fallback to manual pagination
        skip = (page - 1) * per_page
        total = user_model.collection.count_documents(query_filter)
        users_cursor = user_model.collection.find(query_filter).sort(sort_field, sort_direction).skip(skip).limit(per_page)
        users = list(users_cursor)
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    # Format users for template
    formatted_users = []
    subscription_model = SubscriptionPlan()
    
    for user in users:
        # Get subscription info
        subscription_status = user["subscription"]["status"]
        plan_id = user["subscription"].get("planId")
        
        subscription_plan = "None"
        if plan_id:
            plan = subscription_model.get_plan_by_id(plan_id)
            if plan:
                subscription_plan = plan["name"]
        
        # Format for template
        formatted_users.append({
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
    
    # Get stats for filter dropdowns
    total_users = user_model.collection.count_documents({})
    active_users = user_model.collection.count_documents({"isVerified": True})
    inactive_users = user_model.collection.count_documents({"isVerified": False})
    admin_users = user_model.collection.count_documents({"role": "admin"})
    regular_users = user_model.collection.count_documents({"role": "user"})
    
    stats = {
        'total': total_users,
        'active': active_users,
        'inactive': inactive_users,
        'admin': admin_users,
        'user': regular_users
    }
    
    # Get current user for the template
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Create pagination URLs
    pagination_urls = {}
    if page > 1:
        pagination_urls['prev'] = url_for('admin.users', page=page-1, per_page=per_page, 
                                        status=status_filter, role=role_filter, q=search_query, sort=sort_param)
    if page < total_pages:
        pagination_urls['next'] = url_for('admin.users', page=page+1, per_page=per_page, 
                                        status=status_filter, role=role_filter, q=search_query, sort=sort_param)
    
    # Render user management template
    return render_template(
        'admin/users/view.html', 
        users=formatted_users, 
        current_user=current_user,
        stats=stats,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'urls': pagination_urls
        },
        filters={
            'status': status_filter,
            'role': role_filter,
            'search': search_query,
            'sort': sort_param
        },
        title='User Management',
        request=request
    )

def user_create():
    """Create user page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get all subscription plans for the form
    subscription_model = SubscriptionPlan()
    all_plans = subscription_model.list_plans()
    
    if request.method == 'POST':
        # Process form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        is_verified = request.form.get('isVerified') == 'on'
        subscription_status = request.form.get('subscriptionStatus', 'inactive')
        subscription_plan = request.form.get('subscriptionPlan', '')
        
        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template(
                'admin/users/create.html', 
                current_user=current_user,
                title='Create User'
            )
        
        # Create user
        verification_token = None if is_verified else str(uuid.uuid4())
        
        user = user_model.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            verification_token=verification_token
        )
        
        if user:
            # Mark as verified if requested
            if is_verified and verification_token:
                user_model.verify_user(verification_token)
                
            # Set subscription if active
            if subscription_status == 'active' and subscription_plan:
                try:
                    # Set subscription start and end dates
                    start_date = datetime.utcnow()
                    
                    # Get the plan to determine duration
                    plan = subscription_model.get_plan_by_id(subscription_plan)
                    
                    # Default to 30 days if plan not found
                    duration_days = 30
                    if plan:
                        # For simplicity, use monthly duration here
                        duration_days = 30
                    
                    end_date = start_date + timedelta(days=duration_days)
                    
                    # Update user's subscription
                    subscription_data = {
                        'subscription': {
                            'planId': ObjectId(subscription_plan),
                            'status': 'active',
                            'startDate': start_date,
                            'endDate': end_date,
                            'paymentHistory': []
                        }
                    }
                    
                    user_model.update_user(str(user["_id"]), subscription_data)
                    logger.info(f"Admin '{current_user['username']}' assigned subscription plan to user '{username}'")
                except Exception as e:
                    logger.error(f"Error assigning subscription plan: {e}")
                    flash('User created but failed to assign subscription plan', 'warning')
            
            flash('User created successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' created user '{username}'")
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to create user. Username or email may already exist.', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to create user '{username}'")
    
    # Render user create template
    return render_template(
        'admin/users/create.html', 
        current_user=current_user,
        title='Create User'
    )

def user_edit(user_id):
    """Edit user page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get user to edit
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    # Get all subscription plans
    subscription_model = SubscriptionPlan()
    all_plans = subscription_model.list_plans()
    
    # Format plans for select
    formatted_plans = []
    for plan in all_plans:
        formatted_plans.append({
            '_id': str(plan['_id']),
            'name': plan['name'],
            'price': plan['price']
        })
    
    if request.method == 'POST':
        # Process form data
        email = request.form.get('email')
        role = request.form.get('role')
        status = request.form.get('status')
        new_password = request.form.get('new_password')
        subscription_plan = request.form.get('subscription_plan')
        billing_period = request.form.get('billing_period', 'monthly')
        
        # Check if user is trying to downgrade themselves from admin
        if str(user["_id"]) == session['user_id'] and role != 'admin' and user['role'] == 'admin':
            flash('You cannot remove admin privileges from your own account', 'danger')
            return redirect(url_for('admin.user_edit', user_id=user_id))
        
        # Prepare update data
        update_data = {
            'email': email,
            'role': role,
            'isVerified': status == 'active'
        }
        
        # Update user
        success = user_model.update_user(user_id, update_data)

        if success:
            # Handle password change separately if needed
            if new_password and new_password.strip():
                # Hash the password before storing
                hashed_password = user_model.hash_password(new_password)
                
                # Check if update_password method exists, otherwise update directly
                if hasattr(user_model, 'update_password'):
                    password_updated = user_model.update_password(user_id, hashed_password)
                else:
                    try:
                        result = user_model.collection.update_one(
                            {"_id": ObjectId(user_id)},
                            {"$set": {"password": hashed_password}}
                        )
                        password_updated = result.modified_count > 0
                    except Exception as e:
                        logger.error(f"Error updating password: {e}")
                        password_updated = False
                
                if not password_updated:
                    flash('User updated but failed to update password', 'warning')
            
            # Update subscription if needed
            if subscription_plan and subscription_plan != 'none':
                try:
                    # Set subscription start and end dates
                    start_date = datetime.utcnow()
                    
                    # Determine duration based on billing period
                    duration_days = 365 if billing_period == 'yearly' else 30
                    
                    end_date = start_date + timedelta(days=duration_days)
                    
                    # Update user's subscription
                    subscription_data = {
                        'subscription': {
                            'planId': ObjectId(subscription_plan),
                            'status': 'active',
                            'startDate': start_date,
                            'endDate': end_date,
                            # Preserve existing payment history
                            'paymentHistory': user['subscription'].get('paymentHistory', [])
                        }
                    }
                    
                    user_model.update_user(user_id, subscription_data)
                    logger.info(f"Admin '{current_user['username']}' updated subscription for user '{user['username']}'")
                except Exception as e:
                    logger.error(f"Error updating subscription: {e}")
                    flash('User updated but failed to update subscription plan', 'warning')
            elif subscription_plan == 'none':
                # Remove subscription
                subscription_data = {
                    'subscription': {
                        'planId': None,
                        'status': 'inactive',
                        'startDate': None,
                        'endDate': None,
                        # Preserve existing payment history
                        'paymentHistory': user['subscription'].get('paymentHistory', [])
                    }
                }
                user_model.update_user(user_id, subscription_data)
                logger.info(f"Admin '{current_user['username']}' removed subscription for user '{user['username']}'")
                    
            flash('User updated successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' updated user '{user['username']}'")
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to update user', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to update user '{user['username']}'")
    
    # Get current subscription data
    current_plan = None
    current_plan_id = None
    
    if user['subscription']['planId']:
        current_plan_id = str(user['subscription']['planId'])
        plan = subscription_model.get_plan_by_id(current_plan_id)
        if plan:
            current_plan = {
                'name': plan['name'],
                'price': plan['price']
            }
    
    # Format for template
    formatted_user = {
        'id': user["_id"],
        'username': user["username"],
        'email': user["email"],
        'role': user["role"],
        'status': "active" if user.get("isVerified", False) else "inactive",
        'subscription': {
            'status': user['subscription']['status'],
            'plan': current_plan,
            'plan_id': current_plan_id,
            'start_date': user['subscription'].get('startDate').strftime('%Y-%m-%d') if user['subscription'].get('startDate') else None,
            'end_date': user['subscription'].get('endDate').strftime('%Y-%m-%d') if user['subscription'].get('endDate') else None
        }
    }
    
    # Render user edit template
    return render_template(
        'admin/users/edit.html', 
        user=formatted_user, 
        current_user=current_user,
        plans=formatted_plans,
        title='Edit User'
    )

def user_delete(user_id):
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
    # Check if delete_user method exists, otherwise implement directly
    if hasattr(user_model, 'delete_user'):
        success = user_model.delete_user(user_id)
    else:
        try:
            result = user_model.collection.delete_one({"_id": ObjectId(user_id)})
            success = result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            success = False
    
    if success:
        flash('User deleted successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' deleted user '{user['username']}'")
    else:
        flash('Failed to delete user', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to delete user '{user['username']}'")
    
    return redirect(url_for('admin.users'))

def admin_get_user(user_id):
    """API endpoint to get user details for admin."""
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get user to view
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get subscription data
    subscription_model = SubscriptionPlan()
    plan_name = "None"
    if user['subscription']['planId']:
        plan = subscription_model.get_plan_by_id(user['subscription']['planId'])
        if plan:
            plan_name = plan['name']
    
    # Format dates for JSON serialization
    start_date = None
    end_date = None
    if user['subscription'].get('startDate'):
        start_date = user['subscription']['startDate'].strftime('%Y-%m-%d') if isinstance(user['subscription']['startDate'], datetime) else None
    if user['subscription'].get('endDate'):
        end_date = user['subscription']['endDate'].strftime('%Y-%m-%d') if isinstance(user['subscription']['endDate'], datetime) else None
    
    # Prepare user data
    user_data = {
        'id': str(user['_id']),
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'status': 'active' if user.get('isVerified', False) else 'inactive',
        'createdAt': user['createdAt'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(user['createdAt'], datetime) else str(user['createdAt']),
        'subscription': {
            'status': user['subscription']['status'],
            'planId': str(user['subscription']['planId']) if user['subscription'].get('planId') else None,
            'planName': plan_name,
            'startDate': start_date,
            'endDate': end_date
        },
        'villages': user['villages'],
        'settings': user['settings']
    }
    
    logger.info(f"Admin '{current_user['username']}' viewed user '{user['username']}'")
    
    return jsonify({
        'success': True,
        'data': user_data
    })
