# auth/login.py
"""
User login module for Travian Whispers with minimal dependencies.
"""
import base64
import hmac
import hashlib
import json
import time
import logging
from datetime import datetime, timedelta
from database.models.user import User
from flask import session
import config

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auth.login')

def login_user(username_or_email, password, remember_me=False):
    """
    Authenticate a user.
    
    Args:
        username_or_email (str): Username or email
        password (str): Password
        remember_me (bool): Whether to remember login
        
    Returns:
        tuple: (success, message, token, user_data)
    """
    try:
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
        if not user.get("isVerified", False):
            return False, "Please verify your email before logging in", None, None
        
        # Verify password
        if not user_model.verify_password(password, user["password"]):
            logger.warning(f"Failed login attempt for user: {username_or_email}")
            return False, "Invalid username/email or password", None, None
        
        # Generate simple token
        token = generate_simple_token(
            str(user["_id"]), 
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
                "planId": str(user["subscription"]["planId"]) if user["subscription"].get("planId") else None
            }
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return False, f"An error occurred during login: {str(e)}", None, None

def generate_simple_token(user_id, username, email, role):
    """
    Generate a simple signed token without using JWT libraries.
    
    Args:
        user_id (str): User ID
        username (str): Username
        email (str): Email
        role (str): User role
        
    Returns:
        str: Simple token
    """
    expiration = int(time.time()) + (config.JWT_EXPIRATION * 3600)  # Convert hours to seconds
    
    # Create payload
    payload = {
        "user_id": user_id,
        "username": username, 
        "email": email,
        "role": role,
        "exp": expiration,
        "iat": int(time.time())
    }
    
    # Convert to base64
    payload_json = json.dumps(payload)
    payload_bytes = payload_json.encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8')
    
    # Create signature
    key = config.JWT_SECRET.encode('utf-8')
    signature = hmac.new(key, payload_b64.encode('utf-8'), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8')
    
    # Combine payload and signature
    token = f"{payload_b64}.{signature_b64}"
    return token

def logout_user():
    """
    Log out a user by clearing the session.
    
    Returns:
        bool: True if successful
    """
    try:
        if 'user_id' in session:
            user_id = session.get('user_id')
            username = session.get('username', 'Unknown')
            logger.info(f"User logged out successfully: {username} (ID: {user_id})")
            
        # Clear all session data
        session.clear()
        return True
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return False

def verify_simple_token(token):
    """
    Verify a simple token.
    
    Args:
        token (str): Token to verify
        
    Returns:
        dict: Payload if valid, None otherwise
    """
    try:
        # Split token parts
        parts = token.split('.')
        if len(parts) != 2:
            return None
        
        payload_b64, signature_b64 = parts
        
        # Verify signature
        key = config.JWT_SECRET.encode('utf-8')
        expected_signature = hmac.new(key, payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8')
        
        if signature_b64 != expected_signature_b64:
            return None
        
        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        if payload.get('exp', 0) < int(time.time()):
            return None
        
        return payload
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None