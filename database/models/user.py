"""
User model for MongoDB integration.
"""
import re
import uuid
from datetime import datetime, timedelta
from bson import ObjectId
from database.mongodb import MongoDB
from passlib.hash import pbkdf2_sha256
from utils.encryption import encrypt_data, decrypt_data

class User:
    """User model for Travian Whispers application."""
    
    ROLES = ["admin", "user"]
    
    def __init__(self):
        """Initialize the User model."""
        self.db = MongoDB().get_db()
        self.collection = self.db["users"] if self.db else None
    
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
        Hash a password using passlib.
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        return pbkdf2_sha256.hash(password)
    
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
    
    def create_user(self, username, email, password, role="user"):
        """
        Create a new user.
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Plain text password
            role (str): User role (admin or user)
            
        Returns:
            dict: Created user document or None if failed
        """
        if not self.collection:
            return None
            
        # Validate inputs
        if not username or not email or not password:
            return None
            
        if not self.validate_email(email):
            return None
            
        if role not in self.ROLES:
            role = "user"
        
        # Check if username or email already exists
        if self.collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return None
        
        # Create verification token
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
            print(f"Error creating user: {e}")
        
        return None
    
    def get_travian_credentials(self, user_id):
        """
        Get decrypted Travian credentials.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Decrypted credentials or None if not found
        """
        if not self.collection:
            return None
        
        user = self.get_user_by_id(user_id)
        if not user or "travianCredentials" not in user:
            return None
        
        travian_creds = user["travianCredentials"]
        
        return {
            "username": decrypt_data(travian_creds.get("username")),
            "password": decrypt_data(travian_creds.get("password")),
            "tribe": travian_creds.get("tribe"),
            "profileId": travian_creds.get("profileId")
        }
    
    def get_user_by_id(self, user_id):
        """
        Get a user by ID.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User document or None if not found
        """
        if not self.collection:
            return None
            
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except:
            return None
    
    def get_user_by_username(self, username):
        """
        Get a user by username.
        
        Args:
            username (str): Username
            
        Returns:
            dict: User document or None if not found
        """
        if not self.collection:
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
        if not self.collection:
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
        if not self.collection:
            return None
        
        return self.collection.find_one({"verificationToken": token})
    
def get_user_by_reset_token_hash(self, token_hash):
    """
    Get a user by password reset token hash.
    
    Args:
        token_hash (str): Reset token hash
        
    Returns:
        dict: User document or None if not found
    """
    if not self.collection:
        return None
    
    return self.collection.find_one({
        "resetPasswordTokenHash": token_hash,
        "resetPasswordExpires": {"$gt": datetime.utcnow()}
    })

def reset_password_with_hash(self, token_hash, new_password):
    """
    Reset a user's password with token hash.
    
    Args:
        token_hash (str): Reset token hash
        new_password (str): New password
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not self.collection:
        return False
    
    user = self.get_user_by_reset_token_hash(token_hash)
    if not user:
        return False
    
    hashed_password = self.hash_password(new_password)
    
    result = self.collection.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "password": hashed_password,
            "resetPasswordTokenHash": None,
            "resetPasswordExpires": None,
            "updatedAt": datetime.utcnow()
        }}
    )
    
    return result.modified_count > 0
    
    def update_user(self, user_id, update_data):
        """
        Update a user document.
        
        Args:
            user_id (str): User ID
            update_data (dict): Data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
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
            print(f"Error updating user: {e}")
            return False
    
    def verify_user(self, token):
        """
        Verify a user's email with token.
        
        Args:
            token (str): Verification token
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
        
        result = self.collection.update_one(
            {"verificationToken": token},
            {"$set": {"isVerified": True, "verificationToken": None, "updatedAt": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    def create_password_reset(self, email):
        """
        Create a password reset token.
        
        Args:
            email (str): User email
            
        Returns:
            str: Reset token or None if failed
        """
        if not self.collection:
            return None
        
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        reset_token = str(uuid.uuid4())
        expires = datetime.utcnow() + timedelta(hours=24)
        
        result = self.collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "resetPasswordToken": reset_token,
                "resetPasswordExpires": expires,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            return reset_token
        
        return None
    
    def reset_password(self, token, new_password):
        """
        Reset a user's password with token.
        
        Args:
            token (str): Reset token
            new_password (str): New password
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
        
        user = self.get_user_by_reset_token(token)
        if not user:
            return False
        
        hashed_password = self.hash_password(new_password)
        
        result = self.collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password": hashed_password,
                "resetPasswordToken": None,
                "resetPasswordExpires": None,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0
    
    def change_password(self, user_id, current_password, new_password):
        """
        Change a user's password.
        
        Args:
            user_id (str): User ID
            current_password (str): Current password
            new_password (str): New password
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
        
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        if not self.verify_password(current_password, user["password"]):
            return False
        
        hashed_password = self.hash_password(new_password)
        
        result = self.collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
def update_travian_credentials(self, user_id, travian_username, travian_password, tribe=None, profile_id=None):
    """
    Update a user's Travian credentials.
    
    Args:
        user_id (str): User ID
        travian_username (str): Travian username
        travian_password (str): Travian password
        tribe (str, optional): User tribe
        profile_id (str, optional): Profile ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not self.collection:
        return False
    
    # Encrypt the Travian credentials
    encrypted_username = encrypt_data(travian_username)
    encrypted_password = encrypt_data(travian_password)
    
    update_data = {
        "travianCredentials.username": encrypted_username,
        "travianCredentials.password": encrypted_password,
        "updatedAt": datetime.utcnow()
    }
    
    if tribe:
        update_data["travianCredentials.tribe"] = tribe
        
    if profile_id:
        update_data["travianCredentials.profileId"] = profile_id
    
    result = self.collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    return result.modified_count > 0
    
    def update_villages(self, user_id, villages):
        """
        Update a user's villages.
        
        Args:
            user_id (str): User ID
            villages (list): List of village dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "villages": villages,
                    "updatedAt": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def update_subscription(self, user_id, plan_id, status, start_date, end_date):
        """
        Update a user's subscription.
        
        Args:
            user_id (str): User ID
            plan_id (str): Plan ID
            status (str): Subscription status
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "subscription.planId": ObjectId(plan_id) if plan_id else None,
                        "subscription.status": status,
                        "subscription.startDate": start_date,
                        "subscription.endDate": end_date,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating subscription: {e}")
            return False
    
    def add_payment_record(self, user_id, payment_id, amount, method):
        """
        Add a payment record to a user's history.
        
        Args:
            user_id (str): User ID
            payment_id (str): Payment ID
            amount (float): Payment amount
            method (str): Payment method
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        payment_record = {
            "paymentId": payment_id,
            "amount": amount,
            "date": datetime.utcnow(),
            "method": method
        }
        
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$push": {"subscription.paymentHistory": payment_record},
                    "$set": {"updatedAt": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding payment record: {e}")
            return False
    
    def delete_user(self, user_id):
        """
        Delete a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            return False
            
        try:
            result = self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def list_users(self, page=1, limit=20, role=None):
        """
        List users with pagination.
        
        Args:
            page (int): Page number
            limit (int): Number of users per page
            role (str, optional): Filter by role
            
        Returns:
            tuple: (users list, total count)
        """
        if not self.collection:
            return [], 0
            
        skip = (page - 1) * limit
        
        query = {}
        if role and role in self.ROLES:
            query["role"] = role
            
        try:
            cursor = self.collection.find(
                query, 
                {
                    "password": 0,
                    "resetPasswordToken": 0,
                    "resetPasswordExpires": 0,
                    "verificationToken": 0
                }
            ).sort("createdAt", -1).skip(skip).limit(limit)
            
            total = self.collection.count_documents(query)
            
            users = list(cursor)
            return users, total
        except Exception as e:
            print(f"Error listing users: {e}")
            return [], 0
