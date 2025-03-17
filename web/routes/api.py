"""
API routes for Travian Whispers web application.
This module defines the blueprint for API endpoints.
"""
import logging
from flask import Blueprint, request, jsonify, session, current_app
from bson import ObjectId

from web.utils.decorators import login_required, admin_required, api_error_handler
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from payment.paypal import create_subscription_order, process_successful_payment

def jsonify_custom(obj):
    """Custom jsonify function that handles ObjectId and datetime objects."""
    from flask import jsonify
    from web.utils.json_encoder import to_json
    import json
    
    # Convert the object to JSON-serializable data using our custom converter
    serializable_obj = json.loads(json.dumps(obj, default=to_json))
    
    # Use Flask's jsonify with pre-serialized data
    return jsonify(serializable_obj)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/user/profile', methods=['GET'])
@api_error_handler
@login_required
def get_user_profile():
    """API endpoint to get user profile data."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Prepare user profile data
    user_profile = {
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'subscription': {
            'status': user['subscription']['status'],
            'startDate': user['subscription'].get('startDate'),
            'endDate': user['subscription'].get('endDate')
        },
        'settings': {
            'notification': user['settings'].get('notification', True),
            'autoRenew': user['settings'].get('autoRenew', False),
            'autoFarm': user['settings'].get('autoFarm', False),
            'trainer': user['settings'].get('trainer', False)
        },
        'travianCredentials': {
            'username': user['travianCredentials'].get('username', ''),
            'server': user['travianCredentials'].get('server', ''),
            'tribe': user['travianCredentials'].get('tribe', '')
        },
        'villages': user['villages']
    }
    
    return jsonify({
        'success': True,
        'data': user_profile
    })


@api_bp.route('/user/villages', methods=['GET'])
@api_error_handler
@login_required
def get_user_villages():
    """API endpoint to get user villages."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': user['villages']
    })


@api_bp.route('/user/villages/update', methods=['POST'])
@api_error_handler
@login_required
def update_user_villages():
    """API endpoint to update user villages."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get subscription plan
    plan_model = SubscriptionPlan()
    plan = None
    if user['subscription']['planId']:
        plan = plan_model.get_plan_by_id(user['subscription']['planId'])
    
    # Check villages limit
    villages_limit = plan['features']['maxVillages'] if plan else 0
    
    # Get request data
    data = request.get_json()
    villages = data.get('villages', [])
    
    if len(villages) > villages_limit:
        return jsonify({
            'success': False,
            'message': f'You can only have {villages_limit} villages with your current subscription plan'
        }), 400
    
    # Update user villages
    if user_model.update_villages(session['user_id'], villages):
        logger.info(f"User '{user['username']}' updated villages")
        return jsonify({
            'success': True,
            'message': 'Villages updated successfully',
            'data': villages
        })
    else:
        logger.warning(f"Failed to update villages for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to update villages'
        }), 500


@api_bp.route('/user/settings/update', methods=['POST'])
@api_error_handler
@login_required
def update_user_settings():
    """API endpoint to update user settings."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get request data
    data = request.get_json()
    settings = data.get('settings', {})
    
    # Validate settings
    if 'autoFarm' in settings and settings['autoFarm']:
        # Check if user has auto-farm in subscription
        plan_model = SubscriptionPlan()
        plan = None
        if user['subscription']['planId']:
            plan = plan_model.get_plan_by_id(user['subscription']['planId'])
        
        if not plan or not plan['features'].get('autoFarm', False):
            return jsonify({
                'success': False,
                'message': 'Auto-Farm is not included in your subscription plan'
            }), 400
    
    if 'trainer' in settings and settings['trainer']:
        # Check if user has trainer in subscription
        plan_model = SubscriptionPlan()
        plan = None
        if user['subscription']['planId']:
            plan = plan_model.get_plan_by_id(user['subscription']['planId'])
        
        if not plan or not plan['features'].get('trainer', False):
            return jsonify({
                'success': False,
                'message': 'Troop Trainer is not included in your subscription plan'
            }), 400
    
    # Update user settings
    update_data = {
        'settings': {
            # Preserve existing settings
            'notification': user['settings'].get('notification', True),
            'autoRenew': user['settings'].get('autoRenew', False),
            'autoFarm': user['settings'].get('autoFarm', False),
            'trainer': user['settings'].get('trainer', False),
            # Update with new settings
            **settings
        }
    }
    
    if user_model.update_user(session['user_id'], update_data):
        logger.info(f"User '{user['username']}' updated settings")
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'data': update_data['settings']
        })
    else:
        logger.warning(f"Failed to update settings for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to update settings'
        }), 500


@api_bp.route('/user/travian-credentials/update', methods=['POST'])
@api_error_handler
@login_required
def update_travian_credentials():
    """API endpoint to update travian credentials."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get request data
    data = request.get_json()
    travian_credentials = data.get('travianCredentials', {})
    
    # Check if password field is masked
    if travian_credentials.get('password') == '********':
        # Keep existing password
        travian_credentials['password'] = user['travianCredentials'].get('password', '')
    
    # Update travian credentials
    update_data = {
        'travianCredentials': travian_credentials
    }
    
    if user_model.update_user(session['user_id'], update_data):
        logger.info(f"User '{user['username']}' updated Travian credentials")
        return jsonify({
            'success': True,
            'message': 'Travian credentials updated successfully'
        })
    else:
        logger.warning(f"Failed to update Travian credentials for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to update Travian credentials'
        }), 500


@api_bp.route('/subscription/create-order', methods=['POST'])
@api_error_handler
@login_required
def create_subscription_order_route():
    """API endpoint to create a PayPal order for subscription payment."""
    # Get user ID
    user_id = session['user_id']
    
    # Get request data
    data = request.get_json()
    plan_id = data.get('planId')
    
    if not plan_id:
        return jsonify({
            'success': False,
            'message': 'Plan ID is required'
        }), 400
    
    # Generate success and cancel URLs
    base_url = request.host_url.rstrip('/')
    success_url = f"{base_url}/dashboard/subscription/success"
    cancel_url = f"{base_url}/dashboard/subscription/cancel"
    
    # Create PayPal order
    success, order_id, approval_url = create_subscription_order(
        plan_id, 
        user_id, 
        success_url, 
        cancel_url
    )
    
    if success:
        return jsonify({
            'success': True,
            'data': {
                'orderId': order_id,
                'approvalUrl': approval_url
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to create subscription order'
        }), 500


@api_bp.route('/subscription/process-payment', methods=['POST'])
@api_error_handler
@login_required
def process_payment_route():
    """API endpoint to process a PayPal payment."""
    # Get request data
    data = request.get_json()
    order_id = data.get('orderId')
    
    if not order_id:
        return jsonify({
            'success': False,
            'message': 'Order ID is required'
        }), 400
    
    # Process payment
    if process_successful_payment(order_id):
        return jsonify({
            'success': True,
            'message': 'Payment processed successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to process payment'
        }), 500


@api_bp.route('/subscription/cancel', methods=['POST'])
@api_error_handler
@login_required
def cancel_subscription():
    """API endpoint to cancel a subscription."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Check if user has an active subscription
    if user['subscription']['status'] != 'active':
        return jsonify({
            'success': False,
            'message': 'No active subscription to cancel'
        }), 400
    
    # Update subscription status
    if user_model.update_subscription_status(session['user_id'], 'cancelled'):
        logger.info(f"User '{user['username']}' cancelled subscription")
        return jsonify({
            'success': True,
            'message': 'Subscription cancelled successfully'
        })
    else:
        logger.warning(f"Failed to cancel subscription for user '{user['username']}'")
        return jsonify({
            'success': False,
            'message': 'Failed to cancel subscription'
        }), 500


# -----------------------------------------------
# Admin API Routes
# -----------------------------------------------

@api_bp.route('/admin/refresh-stats', methods=['GET'])
@api_error_handler
@admin_required
def admin_refresh_stats():
    """API endpoint to refresh admin dashboard statistics."""
    # In a real implementation, this would recompute the statistics
    
    # Get current user for logging
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    logger.info(f"Admin '{current_user['username']}' refreshed dashboard statistics")
    
    return jsonify({
        'success': True,
        'message': 'Stats refreshed successfully'
    })


@api_bp.route('/admin/create-backup', methods=['POST'])
@api_error_handler
@admin_required
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


@api_bp.route('/admin/update-maintenance', methods=['POST'])
@api_error_handler
@admin_required
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


@api_bp.route('/admin/user/<user_id>', methods=['GET'])
@api_error_handler
@admin_required
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
    
    # Prepare user data
    user_data = {
        'id': str(user['_id']),
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'status': 'active' if user.get('isVerified', False) else 'inactive',
        'createdAt': user['createdAt'],
        'subscription': {
            'status': user['subscription']['status'],
            'planId': str(user['subscription']['planId']) if user['subscription'].get('planId') else None,
            'startDate': user['subscription'].get('startDate'),
            'endDate': user['subscription'].get('endDate')
        },
        'villages': user['villages'],
        'settings': user['settings']
    }
    
    logger.info(f"Admin '{current_user['username']}' viewed user '{user['username']}'")
    
    return jsonify({
        'success': True,
        'data': user_data
    })


@api_bp.route('/webhooks/paypal', methods=['POST'])
@api_error_handler
def paypal_webhook():
    """Webhook endpoint for PayPal payment notifications."""
    # Import PayPal webhook function
    from payment.paypal import handle_webhook_event, verify_webhook_signature
    
    # Verify webhook signature
    if not verify_webhook_signature(request.data, request.headers):
        logger.warning("Invalid PayPal webhook signature")
        return jsonify({
            'success': False,
            'message': 'Invalid webhook signature'
        }), 401
    
    # Get webhook event data
    event_data = request.get_json()
    
    # Extract event type
    event_type = event_data.get('event_type')
    
    if not event_type:
        logger.warning("Missing event type in PayPal webhook")
        return jsonify({
            'success': False,
            'message': 'Missing event type'
        }), 400
    
    # Handle webhook event
    if handle_webhook_event(event_type, event_data):
        logger.info(f"Successfully processed PayPal webhook event: {event_type}")
        return jsonify({
            'success': True,
            'message': 'Webhook processed successfully'
        })
    else:
        logger.warning(f"Failed to process PayPal webhook event: {event_type}")
        return jsonify({
            'success': False,
            'message': 'Failed to process webhook event'
        }), 500