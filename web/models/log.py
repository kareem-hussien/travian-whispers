"""
Activity Log model for Travian Whispers application.
This module provides the ActivityLog model for recording system and user activities.
"""
import logging
import json
from datetime import datetime
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class ActivityLog:
    """ActivityLog model for storing system and user activity logs."""
    
    def __init__(self):
        """Initialize ActivityLog model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["activityLogs"]
    
    def log_activity(self, level, action, details=None, username=None, user_id=None, ip_address=None):
        """
        Log an activity.
        
        Args:
            level (str): Log level (info, warning, error, success)
            action (str): Action description
            details (str, optional): Additional details about the action
            username (str, optional): Username of the related user
            user_id (str, optional): ID of the related user
            ip_address (str, optional): IP address of the user
            
        Returns:
            bool: True if log was created, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        log_data = {
            "timestamp": datetime.utcnow(),
            "level": level.lower(),
            "action": action,
            "details": details,
            "username": username,
            "ip_address": ip_address
        }
        
        # Add user ID if provided
        if user_id:
            try:
                log_data["userId"] = ObjectId(user_id)
            except Exception as e:
                logger.warning(f"Invalid user ID for activity log: {e}")
        
        try:
            result = self.collection.insert_one(log_data)
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return False
    
    def get_recent_logs(self, limit=10):
        """
        Get recent activity logs.
        
        Args:
            limit (int, optional): Maximum number of logs to return
            
        Returns:
            list: List of recent activity logs
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            logs = self.collection.find().sort("timestamp", -1).limit(limit)
            return list(logs)
        except Exception as e:
            logger.error(f"Failed to retrieve activity logs: {e}")
            return []
    
    def get_logs_by_level(self, level, limit=10):
        """
        Get activity logs by level.
        
        Args:
            level (str): Log level to filter by
            limit (int, optional): Maximum number of logs to return
            
        Returns:
            list: List of activity logs with the specified level
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            logs = self.collection.find({"level": level.lower()}).sort("timestamp", -1).limit(limit)
            return list(logs)
        except Exception as e:
            logger.error(f"Failed to retrieve activity logs: {e}")
            return []
    
    def get_logs_by_user(self, user_id, limit=10):
        """
        Get activity logs for a specific user.
        
        Args:
            user_id (str): User ID to filter by
            limit (int, optional): Maximum number of logs to return
            
        Returns:
            list: List of activity logs for the specified user
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            user_oid = ObjectId(user_id)
            logs = self.collection.find({"userId": user_oid}).sort("timestamp", -1).limit(limit)
            return list(logs)
        except Exception as e:
            logger.error(f"Failed to retrieve activity logs: {e}")
            return []
    
    def delete_logs_older_than(self, days):
        """
        Delete logs older than the specified number of days.
        
        Args:
            days (int): Number of days
            
        Returns:
            int: Number of deleted logs
        """
        if self.collection is None:
            logger.error("Database not connected")
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
            result = self.collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old activity logs: {e}")
            return 0
