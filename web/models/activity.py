"""
User Activity model for Travian Whispers application.
This module provides the UserActivity model for recording user-specific activities.
"""
import logging
from datetime import datetime
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class UserActivity:
    """UserActivity model for storing user-specific activity logs."""
    
    def __init__(self):
        """Initialize UserActivity model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["userActivities"]
    
    def log_activity(self, user_id, activity, details=None, status='Success'):
        """
        Log a user activity.
        
        Args:
            user_id (str): User ID
            activity (str): Activity description
            details (str, optional): Additional details
            status (str, optional): Activity status (Success, Warning, Failed, Info)
            
        Returns:
            bool: True if activity was logged, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            user_oid = ObjectId(user_id)
            
            activity_data = {
                "userId": user_oid,
                "timestamp": datetime.utcnow(),
                "activity": activity,
                "details": details,
                "status": status
            }
            
            result = self.collection.insert_one(activity_data)
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to log user activity: {e}")
            return False
    
    def get_recent_activities(self, user_id, limit=10):
        """
        Get recent activities for a user.
        
        Args:
            user_id (str): User ID
            limit (int, optional): Maximum number of activities to return
            
        Returns:
            list: List of recent activities
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            user_oid = ObjectId(user_id)
            activities = self.collection.find({"userId": user_oid}).sort("timestamp", -1).limit(limit)
            return list(activities)
        except Exception as e:
            logger.error(f"Failed to retrieve user activities: {e}")
            return []
    
    def get_user_activities(self, user_id, skip=0, limit=20):
        """
        Get paginated activities for a user.
        
        Args:
            user_id (str): User ID
            skip (int, optional): Number of activities to skip
            limit (int, optional): Maximum number of activities to return
            
        Returns:
            pymongo.cursor.Cursor: Cursor of activities
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            user_oid = ObjectId(user_id)
            activities = self.collection.find(
                {"userId": user_oid}
            ).sort("timestamp", -1).skip(skip).limit(limit)
            return activities
        except Exception as e:
            logger.error(f"Failed to retrieve user activities: {e}")
            return []
    
    def count_user_activities(self, user_id):
        """
        Count total activities for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            int: Total number of activities
        """
        if self.collection is None:
            logger.error("Database not connected")
            return 0
        
        try:
            user_oid = ObjectId(user_id)
            count = self.collection.count_documents({"userId": user_oid})
            return count
        except Exception as e:
            logger.error(f"Failed to count user activities: {e}")
            return 0
    
    def get_activities_by_type(self, user_id, activity_type, limit=10):
        """
        Get activities of a specific type for a user.
        
        Args:
            user_id (str): User ID
            activity_type (str): Activity type to filter by
            limit (int, optional): Maximum number of activities to return
            
        Returns:
            list: List of activities of the specified type
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            user_oid = ObjectId(user_id)
            activities = self.collection.find(
                {"userId": user_oid, "activity": activity_type}
            ).sort("timestamp", -1).limit(limit)
            return list(activities)
        except Exception as e:
            logger.error(f"Failed to retrieve user activities: {e}")
            return []
    
    def delete_activities_older_than(self, days):
        """
        Delete activities older than the specified number of days.
        
        Args:
            days (int): Number of days
            
        Returns:
            int: Number of deleted activities
        """
        if self.collection is None:
            logger.error("Database not connected")
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
            result = self.collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old user activities: {e}")
            return 0
