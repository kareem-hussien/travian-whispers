"""
System log model for Travian Whispers web application.
This module defines the system log model for application-wide logging.
"""
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import DESCENDING
import math

from database.models.init import get_collection

# Initialize logger
logger = logging.getLogger(__name__)

class SystemLog:
    """System log model for application-wide logging."""
    
    def __init__(self):
        """Initialize system log model."""
        self.collection = get_collection('system_logs')
    
    def log_message(self, level, message, user=None, ip_address=None, details=None, category=None):
        """
        Log a system message.
        
        Args:
            level (str): Log level (info, warning, error, debug)
            message (str): Log message
            user (str, optional): Username or user ID
            ip_address (str, optional): IP address of the request
            details (str, optional): Additional details
            category (str, optional): Log category
        
        Returns:
            bool: True if the message was logged successfully, False otherwise
        """
        try:
            # Create log entry
            log_entry = {
                'level': level.lower(),
                'message': message,
                'timestamp': datetime.utcnow()
            }
            
            # Add optional fields
            if user:
                log_entry['user'] = user
            
            if ip_address:
                log_entry['ip_address'] = ip_address
            
            if details:
                log_entry['details'] = details
            
            if category:
                log_entry['category'] = category
            
            # Insert log entry
            result = self.collection.insert_one(log_entry)
            
            return bool(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging system message: {e}")
            return False
    
    def get_logs(self, page=1, per_page=20, level=None, user=None, 
                 category=None, date_from=None, date_to=None):
        """
        Get paginated system logs with optional filtering.
        
        Args:
            page (int): Page number
            per_page (int): Number of logs per page
            level (str, optional): Filter by log level
            user (str, optional): Filter by username
            category (str, optional): Filter by category
            date_from (datetime, optional): Filter by start date
            date_to (datetime, optional): Filter by end date
        
        Returns:
            dict: Dictionary containing logs, pagination info, and total count
        """
        try:
            # Build query
            query = {}
            
            # Apply filters
            if level:
                query['level'] = level.lower()
            
            if user:
                query['user'] = {"$regex": user, "$options": "i"}
            
            if category:
                query['category'] = category
            
            # Handle date range
            if date_from or date_to:
                query['timestamp'] = {}
                
                if date_from:
                    query['timestamp']["$gte"] = date_from
                
                if date_to:
                    query['timestamp']["$lte"] = date_to
            
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
            logger.error(f"Error retrieving system logs: {e}")
            return {
                'logs': [],
                'page': page,
                'per_page': per_page,
                'total': 0,
                'total_pages': 0
            }
    
    def get_log_by_id(self, log_id):
        """
        Get a specific log entry by ID.
        
        Args:
            log_id (str): Log ID
        
        Returns:
            dict: Log details or None if not found
        """
        try:
            return self.collection.find_one({"_id": ObjectId(log_id)})
        except Exception as e:
            logger.error(f"Error retrieving log by ID: {e}")
            return None
    
    def count_logs_by_level(self):
        """
        Count logs grouped by level.
        
        Returns:
            dict: Dictionary with counts for each log level
        """
        try:
            pipeline = [
                {"$group": {"_id": "$level", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            
            results = self.collection.aggregate(pipeline)
            
            # Format results into dictionary
            counts = {
                'info': 0,
                'warning': 0,
                'error': 0,
                'debug': 0
            }
            
            for result in results:
                level = result["_id"]
                if level in counts:
                    counts[level] = result["count"]
            
            # Add total count
            counts['total'] = sum(counts.values())
            
            return counts
        except Exception as e:
            logger.error(f"Error counting logs by level: {e}")
            return {
                'info': 0,
                'warning': 0,
                'error': 0,
                'debug': 0,
                'total': 0
            }
    
    def get_logs_by_timespan(self, hours=24):
        """
        Get logs from the last specified number of hours, grouped by hour.
        
        Args:
            hours (int): Number of hours to look back
        
        Returns:
            list: List of dicts with timestamp and counts by level
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff_time}}},
                {"$group": {
                    "_id": {
                        "hour": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}},
                        "level": "$level"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.hour": 1}}
            ]
            
            results = self.collection.aggregate(pipeline)
            
            # Format results for chart
            formatted_results = {}
            
            for result in results:
                hour = result["_id"]["hour"]
                level = result["_id"]["level"]
                count = result["count"]
                
                if hour not in formatted_results:
                    formatted_results[hour] = {
                        'timestamp': hour,
                        'info': 0,
                        'warning': 0,
                        'error': 0,
                        'debug': 0
                    }
                
                if level in ['info', 'warning', 'error', 'debug']:
                    formatted_results[hour][level] = count
            
            # Convert to list and ensure all hours are present
            current_time = datetime.utcnow()
            
            chart_data = []
            for i in range(hours, 0, -1):
                hour_time = current_time - timedelta(hours=i)
                hour_str = hour_time.strftime("%Y-%m-%d %H:00")
                
                if hour_str in formatted_results:
                    chart_data.append(formatted_results[hour_str])
                else:
                    chart_data.append({
                        'timestamp': hour_str,
                        'info': 0,
                        'warning': 0,
                        'error': 0,
                        'debug': 0
                    })
            
            return chart_data
        except Exception as e:
            logger.error(f"Error retrieving logs by timespan: {e}")
            return []
    
    def delete_logs_older_than(self, days):
        """
        Delete logs older than the specified number of days.
        
        Args:
            days (int): Number of days to keep logs
            
        Returns:
            int: Number of deleted logs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting old logs: {e}")
            return 0
