"""
Settings model for Travian Whispers application.
This module provides the Settings model for managing application settings.
"""
import logging
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class Settings:
    """Settings model for managing application settings."""
    
    def __init__(self):
        """Initialize Settings model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["settings"]
    
    def get_setting(self, key, default=None):
        """
        Get a setting value by key.
        
        Args:
            key (str): Setting key
            default: Default value if setting not found
            
        Returns:
            Setting value or default if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return default
        
        try:
            setting = self.collection.find_one({"key": key})
            
            if setting and "value" in setting:
                return setting["value"]
            
            return default
        except Exception as e:
            logger.error(f"Failed to get setting '{key}': {e}")
            return default
    
    def update_setting(self, key, value):
        """
        Update or create a setting.
        
        Args:
            key (str): Setting key
            value: Setting value
            
        Returns:
            bool: True if setting was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            result = self.collection.update_one(
                {"key": key},
                {"$set": {"value": value}},
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Failed to update setting '{key}': {e}")
            return False
    
    def update_settings(self, settings_dict):
        """
        Update multiple settings at once.
        
        Args:
            settings_dict (dict): Dictionary of settings (key-value pairs)
            
        Returns:
            bool: True if all settings were updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            success = True
            
            for key, value in settings_dict.items():
                result = self.update_setting(key, value)
                if not result:
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False
    
    def delete_setting(self, key):
        """
        Delete a setting.
        
        Args:
            key (str): Setting key
            
        Returns:
            bool: True if setting was deleted, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            result = self.collection.delete_one({"key": key})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete setting '{key}': {e}")
            return False
    
    def get_all_settings(self):
        """
        Get all settings as a dictionary.
        
        Returns:
            dict: Dictionary of all settings (key-value pairs)
        """
        if self.collection is None:
            logger.error("Database not connected")
            return {}
        
        try:
            settings = self.collection.find()
            
            # Convert to dictionary
            settings_dict = {}
            for setting in settings:
                if "key" in setting and "value" in setting:
                    settings_dict[setting["key"]] = setting["value"]
            
            return settings_dict
        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}
    
    def get_settings_by_prefix(self, prefix):
        """
        Get settings that have keys starting with the given prefix.
        
        Args:
            prefix (str): Prefix to match against setting keys
            
        Returns:
            dict: Dictionary of matching settings (key-value pairs)
        """
        if self.collection is None:
            logger.error("Database not connected")
            return {}
        
        try:
            settings = self.collection.find({"key": {"$regex": f"^{prefix}"}})
            
            # Convert to dictionary
            settings_dict = {}
            for setting in settings:
                if "key" in setting and "value" in setting:
                    # Remove prefix from key
                    key = setting["key"].replace(prefix, "", 1)
                    settings_dict[key] = setting["value"]
            
            return settings_dict
        except Exception as e:
            logger.error(f"Failed to get settings with prefix '{prefix}': {e}")
            return {}
