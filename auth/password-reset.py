"""
Password reset module for Travian Whispers.
"""
import logging
import uuid
import re
import hashlib  # Add this import
from datetime import datetime, timedelta
from database.models.user import User
from email_module.sender import send_password_reset_email
from database.error_handler import handle_operation_error, log_database_activity
from utils.encryption import encrypt_data, decrypt_data  # Add this import

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
    raw_reset_token = str(uuid.uuid4())
    # Create a hash of the token to store in the database
    reset_token_hash = hashlib.sha256(raw_reset_token.encode()).hexdigest()
    expires = datetime.utcnow() + timedelta(hours=24)
    
    # Update user record with the hashed token
    update_data = {
        "resetPasswordTokenHash": reset_token_hash,
        "resetPasswordExpires": expires,
        "updatedAt": datetime.utcnow()
    }
    
    if not user_model.update_user(str(user["_id"]), update_data):
        raise PasswordResetError("Failed to create password reset token")
    
    # Generate reset URL with the raw token
    reset_url = f"{reset_url_base}?token={raw_reset_token}"
    
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
    
    # Calculate the hash of the provided token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    user_model = User()
    user = user_model.get_user_by_reset_token_hash(token_hash)
    
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
    
    # Calculate token hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Reset password
    user_model = User()
    if user_model.reset_password_with_hash(token_hash, new_password):
        return True, "Your password has been reset successfully. You can now log in with your new password."
    
    return False, "Failed to reset password"