"""
TroopTrainer model for Travian Whispers application.
This module provides the TroopTrainer model for managing user troop training configurations.
"""
import logging
from datetime import datetime
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class TroopTrainer:
    """TroopTrainer model for managing user troop training configurations."""
    
    def __init__(self):
        """Initialize TroopTrainer model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["troopTrainer"]
    
    def create_config(self, user_id, tribe, troops=None):
        """
        Create a new troop trainer configuration for a user.
        
        Args:
            user_id (str): User ID
            tribe (str): User's tribe (Roman, Teuton, Gaul)
            troops (list, optional): Troop configuration
            
        Returns:
            dict: New troop trainer config or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            
            # Default troop configuration based on tribe
            if troops is None:
                troops = self._get_default_troops(tribe)
            
            config_data = {
                "userId": user_oid,
                "status": "stopped",
                "tribe": tribe,
                "troops": troops,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            # Check if config already exists for this user
            existing = self.collection.find_one({"userId": user_oid})
            
            if existing:
                logger.warning(f"Troop trainer config already exists for user {user_id}")
                return existing
            
            result = self.collection.insert_one(config_data)
            
            if result.inserted_id:
                config_data['_id'] = result.inserted_id
                return config_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to create troop trainer config: {e}")
            return None
    
    def _get_default_troops(self, tribe):
        """
        Get default troop configuration for a tribe.
        
        Args:
            tribe (str): User's tribe (Roman, Teuton, Gaul)
            
        Returns:
            list: Default troop configuration
        """
        if tribe.lower() == "roman":
            return [
                {"name": "Legionnaire", "enabled": True, "quantity": 50, "priority": 1},
                {"name": "Praetorian", "enabled": False, "quantity": 0, "priority": 2},
                {"name": "Imperian", "enabled": False, "quantity": 0, "priority": 3},
                {"name": "Equites Legati", "enabled": False, "quantity": 0, "priority": 2},
                {"name": "Equites Imperatoris", "enabled": False, "quantity": 0, "priority": 3},
                {"name": "Equites Caesaris", "enabled": False, "quantity": 0, "priority": 3}
            ]
        elif tribe.lower() == "teuton":
            return [
                {"name": "Clubswinger", "enabled": True, "quantity": 50, "priority": 1},
                {"name": "Spearman", "enabled": False, "quantity": 0, "priority": 2},
                {"name": "Axeman", "enabled": False, "quantity": 0, "priority": 3},
                {"name": "Scout", "enabled": False, "quantity": 0, "priority": 1},
                {"name": "Paladin", "enabled": False, "quantity": 0, "priority": 3},
                {"name": "Teutonic Knight", "enabled": False, "quantity": 0, "priority": 3}
            ]
        elif tribe.lower() == "gaul":
            return [
                {"name": "Phalanx", "enabled": True, "quantity": 50, "priority": 1},
                {"name": "Swordsman", "enabled": False, "quantity": 0, "priority": 2},
                {"name": "Pathfinder", "enabled": False, "quantity": 0, "priority": 1},
                {"name": "Theutates Thunder", "enabled": False, "quantity": 0, "priority": 3},
                {"name": "Druidrider", "enabled": False, "quantity": 0, "priority": 2},
                {"name": "Haeduan", "enabled": False, "quantity": 0, "priority": 3}
            ]
        else:
            # Default to empty list for unknown tribe
            return []
    
    def get_user_config(self, user_id):
        """
        Get troop trainer configuration for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Troop trainer config or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            config = self.collection.find_one({"userId": user_oid})
            return config
        except Exception as e:
            logger.error(f"Failed to get troop trainer config: {e}")
            return None
    
    def get_user_status(self, user_id):
        """
        Get troop trainer status for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Troop trainer status or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            config = self.collection.find_one(
                {"userId": user_oid},
                {"status": 1, "tribe": 1, "troops": 1}
            )
            return config
        except Exception as e:
            logger.error(f"Failed to get troop trainer status: {e}")
            return None
    
    def update_config(self, user_id, config_data):
        """
        Update troop trainer configuration for a user.
        
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
                # Config doesn't exist, create it with required fields
                if "tribe" not in config_data:
                    # Cannot create config without tribe
                    logger.error("Cannot create troop trainer config without tribe")
                    return False
                
                config_data["userId"] = user_oid
                config_data["createdAt"] = datetime.utcnow()
                
                if "status" not in config_data:
                    config_data["status"] = "stopped"
                
                if "troops" not in config_data:
                    config_data["troops"] = self._get_default_troops(config_data["tribe"])
                
                self.collection.insert_one(config_data)
                return True
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update troop trainer config: {e}")
            return False
    
    def update_status(self, user_id, status):
        """
        Update troop trainer status for a user.
        
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
            
            result = self.collection.update_one(
                {"userId": user_oid},
                {
                    "$set": {
                        "status": status,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                # Config doesn't exist, cannot update
                logger.warning(f"No troop trainer config exists for user {user_id}")
                return False
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update troop trainer status: {e}")
            return False
    
    def update_troops(self, user_id, troops):
        """
        Update troop configuration for a user.
        
        Args:
            user_id (str): User ID
            troops (list): Updated troop configuration
            
        Returns:
            bool: True if troops were updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            user_oid = ObjectId(user_id)
            
            result = self.collection.update_one(
                {"userId": user_oid},
                {
                    "$set": {
                        "troops": troops,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                # Config doesn't exist, cannot update
                logger.warning(f"No troop trainer config exists for user {user_id}")
                return False
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update troop configuration: {e}")
            return False
    
    def get_active_users(self):
        """
        Get all users with active troop trainer.
        
        Returns:
            list: List of user IDs with active troop trainer
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
            logger.error(f"Failed to get active troop trainer users: {e}")
            return []
    
    def delete_config(self, user_id):
        """
        Delete troop trainer configuration for a user.
        
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
            logger.error(f"Failed to delete troop trainer config: {e}")
            return False