"""
User model for MongoDB integration.
"""
import re
import uuid
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from database.mongodb import MongoDB
from passlib.hash import pbkdf2_sha256

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database.models.user')

class User:
    """User model for Travian Whispers application."""
    
    ROLES = ["admin", "user"]
    
    def __init__(self):
        """Initialize the User model."""
        self.db = MongoDB().get_db()
        self.collection = None
        if self.db is not None:  # Explicit None check
            self.collection = self.db["users"]
    
    def validate_email(self, email):
        """
        Validate email format.
        
        Args:
            email (str): Email to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    def hash_password(self, password):
        """
        Hash a password using passlib with improved security parameters.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        # Use stronger hashing parameters (more rounds)
        return pbkdf2_sha256.using(rounds=350000).hash(password)
    
    def verify_password(self, plain_password, hashed_password):
        """
        Verify a password against its hash.
        
        Args:
            plain_password (str): Plain text password
            hashed_password (str): Hashed password
            
        Returns:
            bool: True if match, False otherwise
        """
        return pbkdf2_sha256.verify(plain_password, hashed_password)
    
    def create_user(self, username, email, password, role="user", verification_token=None):
        """
        Create a new user.
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Plain text password
            role (str): User role (admin or user)
            verification_token (str, optional): Verification token
            
        Returns:
            dict: Created user document or None if failed
        """
        if self.collection is None:  # Explicit None check
            return None
            
        # Validate inputs
        if not username or not email or not password:
            return None
            
        if not self.validate_email(email):
            return None
            
        if role not in self.ROLES:
            role = "user"
        
        # Check if username or email already exists
        existing = self.collection.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing is not None:  # Explicit None check
            return None
        
        # Generate verification token if not provided
        if verification_token is None:
            verification_token = str(uuid.uuid4())
        
        # Create user document
        user = {
            "username": username,
            "email": email,
            "password": self.hash_password(password),
            "role": role,
            "isVerified": False,
            "subscription": {
                "planId": None,
                "status": "inactive",
                "startDate": None,
                "endDate": None,
                "paymentHistory": []
            },
            "travianCredentials": {
                "username": "",
                "password": "",
                "tribe": "",
                "profileId": ""
            },
            "villages": [],
            "settings": {
                "autoFarm": False,
                "trainer": False,
                "notification": True
            },
            "verificationToken": verification_token,
            "resetPasswordToken": None,
            "resetPasswordExpires": None,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        try:
            result = self.collection.insert_one(user)
            if result.inserted_id:
                user["_id"] = result.inserted_id
                return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
        
        return None
    
    def get_user_by_id(self, user_id):
        """
        Get a user by ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User document or None if not found
        """
        if self.collection is None:  # Explicit None check
            return None
            
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_username(self, username):
        """
        Get a user by username.
        
        Args:
            username (str): Username
            
        Returns:
            dict: User document or None if not found
        """
        if self.collection is None:  # Explicit None check
            return None
        
        return self.collection.find_one({"username": username})
    
    def get_user_by_email(self, email):
        """
        Get a user by email.
        
        Args:
            email (str): Email address
            
        Returns:
            dict: User document or None if not found
        """
        if self.collection is None:  # Explicit None check
            return None
        
        return self.collection.find_one({"email": email})
    
    def get_user_by_verification_token(self, token):
        """
        Get a user by verification token.
        
        Args:
            token (str): Verification token
            
        Returns:
            dict: User document or None if not found
        """
        if self.collection is None:  # Explicit None check
            logger.warning("User collection is not initialized")
            return None
        
        if not token:
            logger.warning("Empty token provided")
            return None
        
        # Debug: Check token format
        logger.info(f"Looking for user with token: {token}")
        
        # Try to find the user
        user = self.collection.find_one({"verificationToken": token})
        
        if user is None:
            logger.warning(f"No user found with token: {token}")
        else:
            logger.info(f"Found user: {user['username']} with token: {token}")
            
        return user
    
    def get_user_by_reset_token(self, token):
        """
        Get a user by password reset token.
        
        Args:
            token (str): Reset token
            
        Returns:
            dict: User document or None if not found
        """
        if self.collection is None:  # Explicit None check
            return None
        
        return self.collection.find_one({
            "resetPasswordToken": token,
            "resetPasswordExpires": {"$gt": datetime.utcnow()}
        })
    
    def update_user(self, user_id, update_data):
        """
        Update a user document.
        
        Args:
            user_id (str): User ID
            update_data (dict): Data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.collection is None:  # Explicit None check
            return False
            
        try:
            # Don't allow updating some fields directly
            protected_fields = ["_id", "username", "email", "password", "role", "createdAt"]
            for field in protected_fields:
                if field in update_data:
                    del update_data[field]
            
            update_data["updatedAt"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    def verify_user(self, token):
        """
        Verify a user's email with token.
        
        Args:
            token (str): Verification token
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.collection is None:  # Explicit None check
            logger.error("User collection is not initialized")
            return False
        
        try:
            result = self.collection.update_one(
                {"verificationToken": token},
                {"$set": {"isVerified": True, "verificationToken": None, "updatedAt": datetime.utcnow()}}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Successfully verified user with token: {token}")
            else:
                logger.warning(f"Failed to verify user with token: {token}")
                
            return success
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return False

def update_villages(self, user_id, villages):
    """
    Update the villages list for a user.
    
    Args:
        user_id (str): User ID
        villages (list): List of village dictionaries
        
    Returns:
        bool: True if successful, False otherwise
    """
    if self.collection is None:
        logger.error("Database not connected")
        return False
        
    try:
        user_oid = ObjectId(user_id)
        
        result = self.collection.update_one(
            {"_id": user_oid},
            {"$set": {
                "villages": villages,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating villages: {e}")
        return False
    
def merge_villages(self, user_id, new_villages):
    """
    Merge new villages with existing ones, preserving settings.
    
    Args:
        user_id (str): User ID
        new_villages (list): List of newly extracted village dictionaries
        
    Returns:
        bool: True if successful, False otherwise
    """
    if self.collection is None:
        logger.error("Database not connected")
        return False
        
    try:
        # Get user's current villages
        user = self.get_user_by_id(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            return False
            
        current_villages = user.get('villages', [])
        
        # Create a map of existing village settings by newdid
        village_settings = {}
        for village in current_villages:
            newdid = village.get('newdid')
            if newdid:
                village_settings[newdid] = {
                    'auto_farm_enabled': village.get('auto_farm_enabled', False),
                    'training_enabled': village.get('training_enabled', False),
                    'status': village.get('status', 'active')
                }
        
        # Apply existing settings to new villages
        for village in new_villages:
            newdid = village.get('newdid')
            if newdid and newdid in village_settings:
                village['auto_farm_enabled'] = village_settings[newdid]['auto_farm_enabled']
                village['training_enabled'] = village_settings[newdid]['training_enabled']
                village['status'] = village_settings[newdid]['status']
        
        # Update user in database
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "villages": new_villages,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error merging villages: {e}")
        return False