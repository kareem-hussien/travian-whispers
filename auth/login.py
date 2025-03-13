"""
User login module for Travian Whispers.
"""
import jwt
import logging
from datetime import datetime, timedelta
from database.models.user import User

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth.login')

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"  # Change this in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # hours

def generate_token(user_id, username, email, role):
    """
    Generate a JWT token for authenticated user.
    
    Args:
        user_id (str): User ID
        username (str): Username
        email (str): Email
        role (str): User role
        
    Returns:
        str: JWT token
    """
    payload = {
        "user_id": str(user_id),
        "username": username,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """
    Verify a JWT token.
    
    Args:
        token (str): JWT token
        
    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None

def login_user(username_or_email, password):
    """
    Authenticate a user and generate JWT token.
    
    Args:
        username_or_email (str): Username or email
        password (str): Password
        
    Returns:
        tuple: (success, message, token, user_data)
    """
    user_model = User()
    
    # Check if input is email or username
    is_email = "@" in username_or_email
    
    # Get user by email or username
    if is_email:
        user = user_model.get_user_by_email(username_or_email)
    else:
        user = user_model.get_user_by_username(username_or_email)
    
    # Check if user exists
    if not user:
        return False, "Invalid username/email or password", None, None
    
    # Check if user is verified
    if not user["isVerified"]:
        return False, "Please verify your email before logging in", None, None
    
    # Verify password
    if not user_model.verify_password(password, user["password"]):
        return False, "Invalid username/email or password", None, None
    
    # Generate JWT token
    token = generate_token(
        user["_id"], 
        user["username"], 
        user["email"], 
        user["role"]
    )
    
    # Return success with token and user data
    return True, "Login successful", token, {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "subscription": {
            "status": user["subscription"]["status"],
            "planId": str(user["subscription"]["planId"]) if user["subscription"]["planId"] else None
        }
    }

def check_auth(token):
    """
    Check if a token is valid and return user data.
    
    Args:
        token (str): JWT token
        
    Returns:
        tuple: (is_authenticated, user_data)
    """
    if not token:
        return False, None
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        return False, None
    
    # Return user data
    return True, {
        "id": payload["user_id"],
        "username": payload["username"],
        "email": payload["email"],
        "role": payload["role"]
    }

def require_auth(token):
    """
    Decorator-like function to require authentication.
    
    Args:
        token (str): JWT token
        
    Returns:
        tuple: (is_authenticated, user_data)
    """
    return check_auth(token)

def require_admin(token):
    """
    Decorator-like function to require admin role.
    
    Args:
        token (str): JWT token
        
    Returns:
        tuple: (is_admin, user_data)
    """
    is_authenticated, user_data = check_auth(token)
    
    if not is_authenticated or not user_data:
        return False, None
    
    if user_data["role"] != "admin":
        return False, None
    
    return True, user_data
