def get_logs_filtered(self, level=None, username=None, date_from=None, date_to=None, skip=0, limit=50):
    """
    Get filtered logs with pagination.
    
    Args:
        level (str, optional): Log level to filter by
        username (str, optional): Username to filter by
        date_from (datetime, optional): Start date for logs
        date_to (datetime, optional): End date for logs
        skip (int, optional): Number of logs to skip (for pagination)
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: List of filtered logs
    """
    if self.collection is None:
        logger.error("Database not connected")
        return []
    
    try:
        # Build query filter
        query = {}
        
        if level:
            query["level"] = level.lower()
        
        if username:
            query["username"] = {"$regex": username, "$options": "i"}
        
        # Handle date range
        if date_from or date_to:
            query["timestamp"] = {}
            
            if date_from:
                query["timestamp"]["$gte"] = date_from
            
            if date_to:
                query["timestamp"]["$lte"] = date_to
        
        # Get logs with pagination
        logs = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        return list(logs)
    except Exception as e:
        logger.error(f"Failed to get filtered logs: {e}")
        return []

def count_logs_filtered(self, level=None, username=None, date_from=None, date_to=None):
    """
    Count filtered logs.
    
    Args:
        level (str, optional): Log level to filter by
        username (str, optional): Username to filter by
        date_from (datetime, optional): Start date for logs
        date_to (datetime, optional): End date for logs
        
    Returns:
        int: Number of filtered logs
    """
    if self.collection is None:
        logger.error("Database not connected")
        return 0
    
    try:
        # Build query filter
        query = {}
        
        if level:
            query["level"] = level.lower()
        
        if username:
            query["username"] = {"$regex": username, "$options": "i"}
        
        # Handle date range
        if date_from or date_to:
            query["timestamp"] = {}
            
            if date_from:
                query["timestamp"]["$gte"] = date_from
            
            if date_to:
                query["timestamp"]["$lte"] = date_to
        
        # Count logs
        return self.collection.count_documents(query)
    except Exception as e:
        logger.error(f"Failed to count filtered logs: {e}")
        return 0

def get_logs_by_timespan(self, hours=24):
    """
    Get logs from the last specified number of hours.
    
    Args:
        hours (int, optional): Number of hours to look back
        
    Returns:
        list: List of logs from the specified timespan
    """
    if self.collection is None:
        logger.error("Database not connected")
        return []
    
    try:
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = {"timestamp": {"$gte": cutoff_time}}
        
        logs = self.collection.find(query).sort("timestamp", 1)
        return list(logs)
    except Exception as e:
        logger.error(f"Failed to get logs by timespan: {e}")
        return []
    
    __all__ = ['ActivityLog', 'SystemLog']