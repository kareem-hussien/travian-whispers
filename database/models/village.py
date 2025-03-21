"""
Village model for Travian Whispers application.
This module provides the Village model for managing user villages.
"""
import logging
from datetime import datetime
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class Village:
    """Village model for managing user villages."""
    
    def __init__(self):
        """Initialize Village model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["villages"]
    
    def add_village(self, user_id, name, coordinates, population=0, resources=None, status='active'):
        """
        Add a new village for a user.
        
        Args:
            user_id (str): User ID
            name (str): Village name
            coordinates (str): Village coordinates (x|y)
            population (int, optional): Village population
            resources (dict, optional): Village resources
            status (str, optional): Village status
            
        Returns:
            dict: New village document or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            user_oid = ObjectId(user_id)
            
            # Create default resources if not provided
            if resources is None:
                resources = {
                    'wood': 0,
                    'clay': 0,
                    'iron': 0,
                    'crop': 0
                }
            
            village_data = {
                "userId": user_oid,
                "name": name,
                "coordinates": coordinates,
                "population": population,
                "resources": resources,
                "status": status,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            result = self.collection.insert_one(village_data)
            
            if result.inserted_id:
                village_data['_id'] = result.inserted_id
                return village_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to add village: {e}")
            return None
    
    def get_user_villages(self, user_id):
        """
        Get all villages for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of user villages
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            user_oid = ObjectId(user_id)
            villages = self.collection.find({"userId": user_oid})
            return list(villages)
        except Exception as e:
            logger.error(f"Failed to get user villages: {e}")
            return []
    
    def get_village_by_id(self, village_id):
        """
        Get a village by ID.
        
        Args:
            village_id (str): Village ID
            
        Returns:
            dict: Village document or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            village_oid = ObjectId(village_id)
            village = self.collection.find_one({"_id": village_oid})
            return village
        except Exception as e:
            logger.error(f"Failed to get village: {e}")
            return None
    
    def update_village_resources(self, village_id, resources):
        """
        Update village resources.
        
        Args:
            village_id (str): Village ID
            resources (dict): Updated resources
            
        Returns:
            bool: True if resources were updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            village_oid = ObjectId(village_id)
            
            result = self.collection.update_one(
                {"_id": village_oid},
                {
                    "$set": {
                        "resources": resources,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update village resources: {e}")
            return False
    
    def update_village_population(self, village_id, population):
        """
        Update village population.
        
        Args:
            village_id (str): Village ID
            population (int): Updated population
            
        Returns:
            bool: True if population was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            village_oid = ObjectId(village_id)
            
            result = self.collection.update_one(
                {"_id": village_oid},
                {
                    "$set": {
                        "population": population,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update village population: {e}")
            return False
    
    def update_village_status(self, village_id, status):
        """
        Update village status.
        
        Args:
            village_id (str): Village ID
            status (str): Updated status
            
        Returns:
            bool: True if status was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            village_oid = ObjectId(village_id)
            
            result = self.collection.update_one(
                {"_id": village_oid},
                {
                    "$set": {
                        "status": status,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update village status: {e}")
            return False
    
    def delete_village(self, village_id):
        """
        Delete a village.
        
        Args:
            village_id (str): Village ID
            
        Returns:
            bool: True if village was deleted, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            village_oid = ObjectId(village_id)
            
            result = self.collection.delete_one({"_id": village_oid})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete village: {e}")
            return False