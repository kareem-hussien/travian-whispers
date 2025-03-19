"""
AutoFarm model for Travian Whispers application.
This module provides the AutoFarm model for managing user auto-farm configurations.
"""
import logging
from datetime import datetime
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class AutoFarm:
    """AutoFarm model for managing user auto-farm configurations."""
    
    def __init__(self):
        """Initialize AutoFarm model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["autoFarm"]
    
    def create_config(self, user_id, interval=60, active_hours=None, avoid_night=True):
        """
        Create a new auto-farm configuration for a user.
        
        Args:
            user_id (str): User ID
            interval (int, optional): Interval between farm runs in minutes
            active_hours (list, optional): Active hours for auto-farm
            avoid_night (bool, optional): Whether to avoid farming during night hours
            
        Returns:
            dict: New auto-farm config or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            
            # Default active hours (6AM to midnight)
            if active_hours is None:
                active_hours = list(range(6, 24))
            
            config_data = {
                "userId": user_oid,
                "status": "stopped",
                "interval": interval,
                "activeHours": active_hours,
                "avoidNight": avoid_night,
                "useAllFarmLists": True,
                "randomize": 10,  # Default randomization of ±10 minutes
                "lastRun": None,
                "nextRun": None,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            # Check if config already exists for this user
            existing = self.collection.find_one({"userId": user_oid})
            
            if existing:
                logger.warning(f"Auto-farm config already exists for user {user_id}")
                return existing
            
            result = self.collection.insert_one(config_data)
            
            if result.inserted_id:
                config_data['_id'] = result.inserted_id
                return config_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to create auto-farm config: {e}")
            return None
    
    def get_user_config(self, user_id):
        """
        Get auto-farm configuration for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Auto-farm config or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            config = self.collection.find_one({"userId": user_oid})
            return config
        except Exception as e:
            logger.error(f"Failed to get auto-farm config: {e}")
            return None
    
    def get_user_status(self, user_id):
        """
        Get auto-farm status for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Auto-farm status or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            config = self.collection.find_one(
                {"userId": user_oid},
                {"status": 1, "lastRun": 1, "nextRun": 1}
            )
            return config
        except Exception as e:
            logger.error(f"Failed to get auto-farm status: {e}")
            return None
    
    def update_config(self, user_id, config_data):
        """
        Update auto-farm configuration for a user.
        
        Args:
            user_id (str): User ID
            config_data (dict): Updated configuration data
            
        Returns:
            bool: True if config was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            user_oid = ObjectId(user_id)
            
            # Add updated timestamp
            config_data["updatedAt"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"userId": user_oid},
                {"$set": config_data}
            )
            
            if result.matched_count == 0:
                # Config doesn't exist, create it
                config_data["userId"] = user_oid
                config_data["createdAt"] = datetime.utcnow()
                
                if "status" not in config_data:
                    config_data["status"] = "stopped"
                
                self.collection.insert_one(config_data)
                return True
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update auto-farm config: {e}")
            return False
    
    def update_status(self, user_id, status):
        """
        Update auto-farm status for a user.
        
        Args:
            user_id (str): User ID
            status (str): New status (active, stopped, paused)
            
        Returns:
            bool: True if status was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            user_oid = ObjectId(user_id)
            
            # If activating, set next run time
            update_data = {"status": status, "updatedAt": datetime.utcnow()}
            
            if status == "active":
                update_data["nextRun"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"userId": user_oid},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                # Config doesn't exist, create it with default values
                self.create_config(user_id)
                
                # Update status
                self.collection.update_one(
                    {"userId": user_oid},
                    {"$set": update_data}
                )
                return True
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update auto-farm status: {e}")
            return False
    
    def update_last_run(self, user_id, last_run=None):
        """
        Update last run time for a user's auto-farm.
        
        Args:
            user_id (str): User ID
            last_run (datetime, optional): Last run time (defaults to now)
            
        Returns:
            bool: True if last run time was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            user_oid = ObjectId(user_id)
            
            if last_run is None:
                last_run = datetime.utcnow()
            
            result = self.collection.update_one(
                {"userId": user_oid},
                {
                    "$set": {
                        "lastRun": last_run,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update auto-farm last run time: {e}")
            return False
    
    def get_active_users(self):
        """
        Get all users with active auto-farm.
        
        Returns:
            list: List of user IDs with active auto-farm
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            active_configs = self.collection.find({"status": "active"})
            
            # Extract user IDs
            user_ids = [str(config["userId"]) for config in active_configs]
            
            return user_ids
        except Exception as e:
            logger.error(f"Failed to get active auto-farm users: {e}")
            return []
    
    def delete_config(self, user_id):
        """
        Delete auto-farm configuration for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if config was deleted, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            user_oid = ObjectId(user_id)
            
            result = self.collection.delete_one({"userId": user_oid})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete auto-farm config: {e}")
            return False
