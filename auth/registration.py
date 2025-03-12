# auth/registration.py (modified to skip email verification)
"""
Modified user registration module that bypasses email verification.
"""
import logging
from database.models.user import User
from email_module.sender import send_verification_email  # Import still needed but won't send emails

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth.registration')

def register_user(username, email, password, confirm_password, verification_url):
    """
    Register a new user with automatic verification (no email required).
    """
    # Validate username and password
    # ... (keep your existing validation code)
    
    # Initialize user model
    user_model = User()
    
    # Create user
    user = user_model.create_user(username, email, password)
    if not user:
        return False, "Failed to create user", None
    
    # Log verification info but don't require it
    logger.info(f"User registered: {username}, {email} (Auto-verified for development)")
    
    # Auto-verify the user for development purposes
    user_model.verify_user(user["verificationToken"])
    
    # Return success
    return True, "Registration successful! Account automatically verified for development.", {
        "username": user["username"],
        "email": user["email"],
        "isVerified": True  # Force this to true
    }