"""
API endpoint for verifying Travian connection.
"""
import logging
from flask import Blueprint, request, jsonify, session
from web.utils.decorators import login_required, api_error_handler
from database.models.user import User
from database.models.activity_log import ActivityLog

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
travian_api_bp = Blueprint('travian_api', __name__, url_prefix='/api/user/travian')

@travian_api_bp.route('/verify-connection', methods=['POST'])
@api_error_handler
@login_required
def verify_travian_connection():
    """API endpoint to verify Travian account connection."""
    # Get user data
    user_model = User()
    user = user_model.get_user_by_id(session['user_id'])
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get connection details from request
    data = request.get_json()
    
    # Use provided credentials or fall back to stored ones
    username = data.get('username')
    password = data.get('password')
    server_url = data.get('server')
    
    # If password is null, use existing password
    if password is None:
        password = user['travianCredentials'].get('password', '')
    
    # Validate inputs
    if not username:
        return jsonify({
            'success': False,
            'message': 'Username is required'
        }), 400
    
    if not password:
        return jsonify({
            'success': False,
            'message': 'Password is required'
        }), 400
    
    # Try to verify connection
    try:
        # Test the connection
        connection_result = test_connection(
            username, 
            password, 
            server_url
        )
        
        # Check connection result
        if connection_result['success']:
            # Get villages count if available
            villages_count = connection_result.get('villages_count', 0)
            
            # Log successful connection
            try:
                activity_model = ActivityLog()
                activity_model.log_activity(
                    user_id=session['user_id'],
                    activity_type='travian-connection',
                    details='Successfully connected to Travian account',
                    status='success',
                    data={
                        'villages_count': villages_count
                    }
                )
            except Exception as e:
                logger.error(f"Error logging connection activity: {e}")
            
            # Return success response
            return jsonify({
                'success': True,
                'message': 'Travian account successfully connected!',
                'villages_count': villages_count
            })
        else:
            # Log failed connection
            try:
                activity_model = ActivityLog()
                activity_model.log_activity(
                    user_id=session['user_id'],
                    activity_type='travian-connection',
                    details=f"Failed to connect to Travian account: {connection_result.get('message', 'Unknown error')}",
                    status='error'
                )
            except Exception as e:
                logger.error(f"Error logging connection activity: {e}")
            
            # Return error response
            return jsonify({
                'success': False,
                'message': connection_result.get('message', 'Failed to connect to Travian account')
            })
    except Exception as e:
        logger.error(f"Error verifying Travian connection: {e}")
        
        # Log error
        try:
            activity_model = ActivityLog()
            activity_model.log_activity(
                user_id=session['user_id'],
                activity_type='travian-connection',
                details=f"Error verifying Travian connection: {str(e)}",
                status='error'
            )
        except Exception as log_err:
            logger.error(f"Error logging connection activity: {log_err}")
        
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500

def register_routes(app):
    """Register Travian API routes with the application."""
    app.register_blueprint(travian_api_bp)
