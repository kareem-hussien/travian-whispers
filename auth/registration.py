"""
User registration module for Travian Whispers.
"""
import re
import logging
import uuid
from datetime import datetime
from database.models.user import User
from email_module.sender import send_verification_email
from database.error_handler import handle_operation_error, log_database_activity

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth.registration')

class RegistrationError(Exception):
    """Base class for registration-related errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def validate_username(username):
    """
    Validate username format.
    
    Args:
        username (str): Username to validate
        
    Returns:
        tuple: (is_valid, message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be 3-20 characters long"
    
    # Username must start with a letter and contain only letters, numbers, and underscores
    pattern = r"^[a-zA-Z][a-zA-Z0-9_]{2,19}$"
    if not re.match(pattern, username):
        return False, "Username must start with a letter and contain only letters, numbers, and underscores"
    
    return True, "Username is valid"

def validate_password(password, confirm_password=None):
    """
    Validate password strength and match.
    
    Args:
        password (str): Password to validate
        confirm_password (str, optional): Confirmation password
        
    Returns:
        tuple: (is_valid, message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Password should have at least one uppercase letter, one lowercase letter, and one digit
    if not (re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'\d', password)):
        return False, "Password must contain at least one uppercase letter, one lowercase letter, and one digit"
    
    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match"
    
    return True, "Password is valid"

@handle_operation_error
@log_database_activity("user registration")
def register_user(username, email, password, confirm_password, verification_url_base):
    """
    Register a new user.
    
    Args:
        username (str): Username
        email (str): Email address
        password (str): Password
        confirm_password (str): Confirm password
        verification_url_base (str): Base URL for email verification
        
    Returns:
        tuple: (success, message, user_data)
    """
    try:
        # Validate inputs
        is_valid_username, username_message = validate_username(username)
        if not is_valid_username:
            return False, username_message, None
        
        is_valid_password, password_message = validate_password(password, confirm_password)
        if not is_valid_password:
            return False, password_message, None
        
        # Initialize user model
        user_model = User()
        
        # Check if collection is available
        if user_model.collection is None:
            return False, "Database connection error", None
        
        # Check if username or email already exists
        existing_user = user_model.get_user_by_username(username)
        if existing_user is not None:  # Explicit None check
            return False, "Username already exists", None
        
        existing_email = user_model.get_user_by_email(email)
        if existing_email is not None:  # Explicit None check
            return False, "Email address already exists", None
        
        # Generate verification token
        verification_token = str(uuid.uuid4())
        
        # Create user with token
        user = user_model.create_user(username, email, password, verification_token=verification_token)
        if user is None:  # Explicit None check
            return False, "Failed to create user", None
        
        # Log token
        logger.info(f"User {username} created with verification token: {verification_token}")
        
        # Generate verification URL
        verification_url = f"{verification_url_base}{verification_token}"
        
        # Send verification email
        try:
            send_verification_email(email, username, verification_url)
            logger.info(f"Verification email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            # Continue registration process even if email sending fails
        
        # Return success
        return True, "Registration successful! Please check your email to verify your account.", {
            "username": user["username"],
            "email": user["email"],
            "isVerified": user["isVerified"]
        }
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False, "An error occurred during registration. Please try again.", None