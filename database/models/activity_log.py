"""
Activity log model for Travian Whispers web application.
This module defines the activity log model for tracking user activities.
"""
import logging
from datetime import datetime
from bson import ObjectId
from pymongo import DESCENDING
import math

from database.models.init import get_collection

# Initialize logger
logger = logging.getLogger(__name__)

class ActivityLog:
    """Activity log model for tracking user activities."""
    
    def __init__(self):
        """Initialize activity log model."""
        self.collection = get_collection('activity_logs')
    
    def log_activity(self, user_id, activity_type, details=None, status='success', village=None, data=None):
        """
        Log a user activity.
        
        Args:
            user_id (str): User ID
            activity_type (str): Type of activity (e.g., 'auto-farm', 'troop-training', 'login', 'profile-update')
            details (str): Details of the activity
            status (str): Status of the activity (success, warning, error, info)
            village (str): Village name or ID (optional)
            data (dict): Additional data for the activity (optional)
        
        Returns:
            bool: True if the activity was logged successfully, False otherwise
        """
        try:
            # Create log entry
            log_entry = {
                'userId': user_id,
                'activityType': activity_type,
                'details': details or f"{activity_type.replace('-', ' ').title()} activity",
                'status': status,
                'timestamp': datetime.utcnow()
            }
            
            # Add optional fields
            if village:
                log_entry['village'] = village
            
            if data:
                log_entry['data'] = data
            
            # Insert log entry
            result = self.collection.insert_one(log_entry)
            
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    def get_user_logs(self, user_id, page=1, per_page=20, filter_query=None):
        """
        Get paginated user activity logs.
        
        Args:
            user_id (str): User ID
            page (int): Page number
            per_page (int): Number of logs per page
            filter_query (dict): Additional filter criteria
        
        Returns:
            dict: Dictionary containing logs, pagination info, and total count
        """
        try:
            # Build query
            query = {'userId': user_id}
            
            # Add additional filter criteria if provided
            if filter_query:
                query.update(filter_query)
            
            # Get total count
            total = self.collection.count_documents(query)
            
            # Calculate pagination
            total_pages = math.ceil(total / per_page)
            skip = (page - 1) * per_page
            
            # Get logs
            logs = list(self.collection.find(query)
                         .sort('timestamp', DESCENDING)
                         .skip(skip)
                         .limit(per_page))
            
            return {
                'logs': logs,
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            }
        except Exception as e:
            logger.error(f"Error getting user logs: {e}")
            return {
                'logs': [],
                'page': page,
                'per_page': per_page,
                'total': 0,
                'total_pages': 0
            }
    
    def get_latest_user_activity(self, user_id, activity_type=None, village=None, filter_query=None):
        """
        Get the latest user activity of a specific type.
        
        Args:
            user_id (str): User ID
            activity_type (str): Type of activity (optional)
            village (str): Village name or ID to filter by (optional)
            filter_query (dict): Additional filter criteria (optional)
        
        Returns:
            dict: Latest activity log or None if not found
        """
        try:
            # Build query
            query = {'userId': user_id}
            
            # Add activity type if provided
            if activity_type:
                query['activityType'] = activity_type
            
            # Add village filter if provided
            if village:
                query['village'] = village
                
            # Add additional filter criteria if provided
            if filter_query:
                query.update(filter_query)
            
            # Get latest activity
            activity = self.collection.find_one(
                query,
                sort=[('timestamp', DESCENDING)]
            )
            
            return activity
        except Exception as e:
            logger.error(f"Error getting latest user activity: {e}")
            return None
    
    def count_user_activities(self, user_id, activity_type=None, status=None):
        """
        Count user activities by type or status.
        
        Args:
            user_id (str): User ID
            activity_type (str): Type of activity (optional)
            status (str): Status of activity (optional)
        
        Returns:
            int: Count of activities
        """
        try:
            # Build query
            query = {'userId': user_id}
            
            # Add activity type if provided
            if activity_type:
                query['activityType'] = activity_type
            
            # Add status if provided
            if status:
                query['status'] = status
            
            # Count activities
            count = self.collection.count_documents(query)
            
            return count
        except Exception as e:
            logger.error(f"Error counting user activities: {e}")
            return 0
    
    def delete_user_logs(self, user_id):
        """
        Delete all logs for a user.
        
        Args:
            user_id (str): User ID
        
        Returns:
            bool: True if logs were deleted successfully, False otherwise
        """
        try:
            # Delete logs
            result = self.collection.delete_many({'userId': user_id})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user logs: {e}")
            return False
