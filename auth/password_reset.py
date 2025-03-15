"""
Password reset module for Travian Whispers.
"""
import logging
import uuid
import re
from datetime import datetime, timedelta
from database.models.user import User
from email_module.sender import send_password_reset_email
from database.error_handler import handle_operation_error, log_database_activity

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth.password_reset')

class PasswordResetError(Exception):
    """Base class for password reset-related errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def validate_password_strength(password):
    """
    Validate password strength.
    
    Password must:
    - Be at least 8 characters long
    - Contain at least one uppercase letter
    - Contain at least one lowercase letter
    - Contain at least one digit
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is strong"

@handle_operation_error
@log_database_activity("password reset request")
def request_password_reset(email, reset_url_base):
    """
    Request a password reset for a user.
    
    Args:
        email (str): User email
        reset_url_base (str): Base URL for password reset page
        
    Returns:
        tuple: (success, message)
    """
    if not email:
        raise PasswordResetError("Email is required")
    
    user_model = User()
    user = user_model.get_user_by_email(email)
    
    if not user:
        # For security reasons, don't reveal that the email doesn't exist
        return True, "If your email exists in our system, you will receive password reset instructions."
    
    # Generate reset token and set expiration (24 hours)
    reset_token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=24)
    
    # Update user record
    update_data = {
        "resetPasswordToken": reset_token,
        "resetPasswordExpires": expires,
        "updatedAt": datetime.utcnow()
    }
    
    if not user_model.update_user(str(user["_id"]), update_data):
        raise PasswordResetError("Failed to create password reset token")
    
    # Generate reset URL
    reset_url = f"{reset_url_base}?token={reset_token}"
    
    # Send reset email
    try:
        send_password_reset_email(user["email"], user["username"], reset_url)
        return True, "Password reset instructions have been sent to your email."
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        raise PasswordResetError("Failed to send password reset email")

@handle_operation_error
@log_database_activity("password reset validation")
def validate_reset_token(token):
    """
    Validate a password reset token.
    
    Args:
        token (str): Reset token
        
    Returns:
        tuple: (is_valid, user_data)
    """
    if not token:
        return False, None
    
    user_model = User()
    user = user_model.get_user_by_reset_token(token)
    
    if not user:
        return False, None
    
    # Check if token is expired
    if user["resetPasswordExpires"] < datetime.utcnow():
        return False, None
    
    return True, {
        "user_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"]
    }

@handle_operation_error
@log_database_activity("password reset")
def reset_password(token, new_password, confirm_password):
    """
    Reset a user's password with token.
    
    Args:
        token (str): Reset token
        new_password (str): New password
        confirm_password (str): Password confirmation
        
    Returns:
        tuple: (success, message)
    """
    # Validate token
    is_valid, user_data = validate_reset_token(token)
    if not is_valid:
        return False, "Invalid or expired password reset token"
    
    # Validate passwords match
    if new_password != confirm_password:
        return False, "Passwords do not match"
    
    # Validate password strength
    is_strong, message = validate_password_strength(new_password)
    if not is_strong:
        return False, message
    
    # Reset password
    user_model = User()
    if user_model.reset_password(token, new_password):
        return True, "Your password has been reset successfully. You can now log in with your new password."
    
    return False, "Failed to reset password"

@handle_operation_error
@log_database_activity("password change")
def change_password(user_id, current_password, new_password, confirm_password):
    """
    Change a user's password.
    
    Args:
        user_id (str): User ID
        current_password (str): Current password
        new_password (str): New password
        confirm_password (str): Password confirmation
        
    Returns:
        tuple: (success, message)
    """
    # Validate passwords match
    if new_password != confirm_password:
        return False, "New passwords do not match"
    
    # Validate password strength
    is_strong, message = validate_password_strength(new_password)
    if not is_strong:
        return False, message
    
    # Change password
    user_model = User()
    if user_model.change_password(user_id, current_password, new_password):
        return True, "Your password has been changed successfully."
    
    return False, "Current password is incorrect or password change failed"

@handle_operation_error
@log_database_activity("reset token cleanup")
def cleanup_expired_tokens():
    """
    Clean up expired password reset tokens.
    
    Returns:
        int: Number of tokens cleaned up
    """
    user_model = User()
    
    # Get current time
    now = datetime.utcnow()
    
    # In a real implementation, this would use the database's update_many
    # to update all matching records in a single operation
    users_collection = user_model.collection
    result = users_collection.update_many(
        {
            "resetPasswordToken": {"$ne": None},
            "resetPasswordExpires": {"$lt": now}
        },
        {
            "$set": {
                "resetPasswordToken": None,
                "resetPasswordExpires": None,
                "updatedAt": now
            }
        }
    )
    
    return result.modified_count
