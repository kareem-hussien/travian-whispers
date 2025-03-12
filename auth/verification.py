"""
Email verification module for Travian Whispers.
"""
import logging
import uuid
from datetime import datetime, timedelta
from database.models.user import User
from email.sender import send_verification_email, send_welcome_email
from database.error_handler import handle_operation_error, log_database_activity

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth.verification')

class VerificationError(Exception):
    """Base class for verification-related errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

@handle_operation_error
@log_database_activity("verification")
def create_verification_token(user_id):
    """Generate a new verification token for a user."""
    # Generate a secure token using the encryption utilities
    raw_token = str(uuid.uuid4())
    # Store only the hash of the token in the database
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Update user with hashed token
    update_data = {
        "verificationTokenHash": hashed_token,
        "updatedAt": datetime.utcnow()
    }
    
    if user_model.update_user(user_id, update_data):
        # Return the raw token to be included in the email
        return raw_token
    
    return None
    
    # Generate new token
    verification_token = str(uuid.uuid4())
    
    # Update user record
    update_data = {
        "verificationToken": verification_token,
        "updatedAt": datetime.utcnow()
    }
    
    if user_model.update_user(user_id, update_data):
        return verification_token
    
    raise VerificationError(f"Failed to update verification token for user: {user_id}")

@handle_operation_error
@log_database_activity("verification")
def verify_email_token(token):
    """
    Verify a user's email with token.
    
    Args:
        token (str): Verification token
        
    Returns:
        tuple: (success, message, user_data)
    """
    if not token:
        raise VerificationError("Invalid verification token")
    
    user_model = User()
    user = user_model.get_user_by_verification_token(token)
    
    if not user:
        raise VerificationError("Invalid or expired verification token")
    
    if user["isVerified"]:
        return True, "Your email is already verified", {
            "username": user["username"],
            "email": user["email"]
        }
    
    # Update user verification status
    if user_model.verify_user(token):
        # Send welcome email
        try:
            send_welcome_email(user["email"], user["username"])
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            # Continue as this is not critical
        
        return True, "Email verified successfully! You can now log in.", {
            "username": user["username"],
            "email": user["email"]
        }
    
    raise VerificationError("Failed to verify email")

@handle_operation_error
@log_database_activity("verification")
def resend_verification_email(email):
    """
    Resend verification email to a user.
    
    Args:
        email (str): User email
        
    Returns:
        tuple: (success, message)
    """
    user_model = User()
    user = user_model.get_user_by_email(email)
    
    if not user:
        raise VerificationError(f"User not found with email: {email}")
    
    if user["isVerified"]:
        return False, "Your email is already verified. You can log in."
    
    # If no verification token exists, create one
    verification_token = user["verificationToken"]
    if not verification_token:
        verification_token = create_verification_token(str(user["_id"]))
    
    # Generate verification URL
    # In a real app, this would be a configuration or environment variable
    base_url = "https://travian-whispers.com/verify"
    verification_url = f"{base_url}?token={verification_token}"
    
    # Send verification email
    try:
        send_verification_email(user["email"], user["username"], verification_url)
        return True, "Verification email has been resent. Please check your inbox."
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise VerificationError("Failed to send verification email")

@handle_operation_error
@log_database_activity("verification")
def get_verification_status(user_id):
    """
    Get verification status for a user.
    
    Args:
        user_id (str): User ID
        
    Returns:
        bool: True if verified, False otherwise
    """
    user_model = User()
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        raise VerificationError(f"User not found with ID: {user_id}")
    
    return user["isVerified"]

@handle_operation_error
@log_database_activity("verification cleanup")
def cleanup_expired_verifications():
    """
    Clean up expired verification tokens.
    
    Returns:
        int: Number of tokens cleaned up
    """
    user_model = User()
    
    # Get users with verification tokens older than 7 days
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    
    # In a real implementation, this would use the database's update_many
    # to update all matching records in a single operation
    users_collection = user_model.collection
    result = users_collection.update_many(
        {
            "verificationToken": {"$ne": None},
            "isVerified": False,
            "createdAt": {"$lt": seven_days_ago}
        },
        {
            "$set": {
                "verificationToken": None,
                "updatedAt": now
            }
        }
    )
    
    return result.modified_count
