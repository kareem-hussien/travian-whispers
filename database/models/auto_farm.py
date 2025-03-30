"""
Auto farm configuration model for Travian Whispers web application.
This module defines the auto farm configuration model.
"""
import logging
from datetime import datetime
from bson import ObjectId

from database.models.init import get_collection

# Initialize logger
logger = logging.getLogger(__name__)

class AutoFarmConfiguration:
    """Auto farm configuration model."""
    
    def __init__(self):
        """Initialize auto farm configuration model."""
        self.collection = get_collection('auto_farm_configurations')
    
    def get_user_configuration(self, user_id):
        """
        Get auto farm configuration for a user.
        
        Args:
            user_id (str): User ID
        
        Returns:
            dict: Auto farm configuration or None if not found
        """
        try:
            # Get configuration
            config = self.collection.find_one({'userId': user_id})
            
            return config
        except Exception as e:
            logger.error(f"Error getting auto farm configuration: {e}")
            return None
    
    def create_or_update_configuration(self, user_id, config_data):
        """
        Create or update auto farm configuration.
        
        Args:
            user_id (str): User ID
            config_data (dict): Configuration data
        
        Returns:
            bool: True if configuration was created/updated successfully, False otherwise
        """
        try:
            # Add userId and updatedAt fields
            config_data['userId'] = user_id
            config_data['updatedAt'] = datetime.utcnow()
            
            # Check if configuration exists
            existing_config = self.collection.find_one({'userId': user_id})
            
            if existing_config:
                # Update existing configuration
                result = self.collection.update_one(
                    {'userId': user_id},
                    {'$set': config_data}
                )
                
                return result.modified_count > 0
            else:
                # Create new configuration
                config_data['createdAt'] = datetime.utcnow()
                result = self.collection.insert_one(config_data)
                
                return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating/updating auto farm configuration: {e}")
            return False
    
    def delete_configuration(self, user_id):
        """
        Delete auto farm configuration.
        
        Args:
            user_id (str): User ID
        
        Returns:
            bool: True if configuration was deleted successfully, False otherwise
        """
        try:
            # Delete configuration
            result = self.collection.delete_one({'userId': user_id})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting auto farm configuration: {e}")
            return False
            
    def update_farm_list(self, user_id, farm_list_id, farm_list_data):
        """
        Update a specific farm list in the configuration.
        
        Args:
            user_id (str): User ID
            farm_list_id (str): Farm list ID
            farm_list_data (dict): Farm list data
        
        Returns:
            bool: True if farm list was updated successfully, False otherwise
        """
        try:
            # Get existing configuration
            config = self.collection.find_one({'userId': user_id})
            
            if not config:
                return False
            
            # Get farm lists
            farm_lists = config.get('farmLists', [])
            
            # Find farm list index
            farm_list_idx = -1
            for i, farm_list in enumerate(farm_lists):
                if str(farm_list.get('id')) == str(farm_list_id):
                    farm_list_idx = i
                    break
            
            if farm_list_idx >= 0:
                # Update existing farm list
                update_path = f'farmLists.{farm_list_idx}'
                result = self.collection.update_one(
                    {'userId': user_id},
                    {
                        '$set': {
                            update_path: farm_list_data,
                            'updatedAt': datetime.utcnow()
                        }
                    }
                )
                
                return result.modified_count > 0
            else:
                # Add new farm list
                farm_list_data['id'] = ObjectId()
                result = self.collection.update_one(
                    {'userId': user_id},
                    {
                        '$push': {'farmLists': farm_list_data},
                        '$set': {'updatedAt': datetime.utcnow()}
                    }
                )
                
                return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating farm list: {e}")
            return False
    
    def delete_farm_list(self, user_id, farm_list_id):
        """
        Delete a farm list from the configuration.
        
        Args:
            user_id (str): User ID
            farm_list_id (str): Farm list ID
        
        Returns:
            bool: True if farm list was deleted successfully, False otherwise
        """
        try:
            # Delete farm list
            result = self.collection.update_one(
                {'userId': user_id},
                {
                    '$pull': {'farmLists': {'id': ObjectId(farm_list_id)}},
                    '$set': {'updatedAt': datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting farm list: {e}")
            return False
