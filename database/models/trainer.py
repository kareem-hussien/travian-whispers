"""
Troop trainer configuration model for Travian Whispers web application.
This module defines the troop trainer configuration model.
"""
import logging
from datetime import datetime
from bson import ObjectId

from database.models.init import get_collection

# Initialize logger
logger = logging.getLogger(__name__)

class TrainerConfiguration:
    """Troop trainer configuration model."""
    
    def __init__(self):
        """Initialize troop trainer configuration model."""
        self.collection = get_collection('trainer_configurations')
    
    def get_user_configuration(self, user_id):
        """
        Get troop trainer configuration for a user.
        
        Args:
            user_id (str): User ID
        
        Returns:
            dict: Troop trainer configuration or None if not found
        """
        try:
            # Get configuration
            config = self.collection.find_one({'userId': user_id})
            
            return config
        except Exception as e:
            logger.error(f"Error getting troop trainer configuration: {e}")
            return None
    
    def create_or_update_configuration(self, user_id, config_data):
        """
        Create or update troop trainer configuration.
        
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
            logger.error(f"Error creating/updating troop trainer configuration: {e}")
            return False
    
    def delete_configuration(self, user_id):
        """
        Delete troop trainer configuration.
        
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
            logger.error(f"Error deleting troop trainer configuration: {e}")
            return False
    
    def update_troop_settings(self, user_id, troop_id, troop_data):
        """
        Update settings for a specific troop type.
        
        Args:
            user_id (str): User ID
            troop_id (str): Troop type identifier
            troop_data (dict): Troop configuration data
        
        Returns:
            bool: True if troop settings were updated successfully, False otherwise
        """
        try:
            # Get existing configuration
            config = self.collection.find_one({'userId': user_id})
            
            if not config:
                return False
            
            # Get troops configuration
            troops = config.get('troops', [])
            
            # Find troop index
            troop_idx = -1
            for i, troop in enumerate(troops):
                if troop.get('type') == troop_id:
                    troop_idx = i
                    break
            
            if troop_idx >= 0:
                # Update existing troop settings
                update_path = f'troops.{troop_idx}'
                result = self.collection.update_one(
                    {'userId': user_id},
                    {
                        '$set': {
                            update_path: troop_data,
                            'updatedAt': datetime.utcnow()
                        }
                    }
                )
                
                return result.modified_count > 0
            else:
                # Add new troop settings
                result = self.collection.update_one(
                    {'userId': user_id},
                    {
                        '$push': {'troops': troop_data},
                        '$set': {'updatedAt': datetime.utcnow()}
                    }
                )
                
                return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating troop settings: {e}")
            return False
    
    def update_queue(self, user_id, queue_data):
        """
        Update the training queue.
        
        Args:
            user_id (str): User ID
            queue_data (list): Training queue data
        
        Returns:
            bool: True if queue was updated successfully, False otherwise
        """
        try:
            # Update queue
            result = self.collection.update_one(
                {'userId': user_id},
                {
                    '$set': {
                        'queue': queue_data,
                        'updatedAt': datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Error updating training queue: {e}")
            return False
