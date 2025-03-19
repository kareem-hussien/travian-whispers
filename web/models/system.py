"""
System Status model for Travian Whispers application.
This module provides the SystemStatus model for system monitoring and maintenance.
"""
import logging
import os
import psutil
from datetime import datetime
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class SystemStatus:
    """SystemStatus model for storing and retrieving system status information."""
    
    def __init__(self):
        """Initialize SystemStatus model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["systemStatus"]
    
    def update_status(self, status_data):
        """
        Update system status.
        
        Args:
            status_data (dict): System status data
            
        Returns:
            bool: True if status was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            # Add timestamp if not provided
            if 'timestamp' not in status_data:
                status_data['timestamp'] = datetime.utcnow()
            
            # Try to update existing status document, or insert if none exists
            result = self.collection.update_one(
                {"_id": "current_status"},
                {"$set": status_data},
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Failed to update system status: {e}")
            return False
    
    def get_current_status(self):
        """
        Get current system status.
        
        Returns:
            dict: Current system status or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            status = self.collection.find_one({"_id": "current_status"})
            return status
        except Exception as e:
            logger.error(f"Failed to retrieve system status: {e}")
            return None
    
    def collect_system_metrics(self):
        """
        Collect current system metrics and update status.
        
        Returns:
            bool: True if metrics were collected and status updated, False otherwise
        """
        try:
            process = psutil.Process(os.getpid())
            
            # Calculate uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            days, remainder = divmod(uptime.total_seconds(), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m"
            
            # Calculate memory usage
            memory_info = process.memory_info()
            memory_usage = (memory_info.rss / psutil.virtual_memory().total) * 100
            
            # Calculate CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Calculate disk usage
            disk_usage = psutil.disk_usage('/').percent
            
            # Get active connections
            active_connections = len(psutil.net_connections())
            
            # Determine system status based on metrics
            if memory_usage > 90 or cpu_usage > 90 or disk_usage > 90:
                status = "Critical"
            elif memory_usage > 75 or cpu_usage > 75 or disk_usage > 75:
                status = "Warning"
            else:
                status = "Healthy"
            
            # Build status data
            status_data = {
                "timestamp": datetime.utcnow(),
                "status": status,
                "uptime": uptime_str,
                "memory_usage": round(memory_usage, 1),
                "cpu_usage": cpu_usage,
                "disk_usage": disk_usage,
                "active_connections": active_connections,
                "maintenance_mode": current_app.config.get('MAINTENANCE_MODE', False),
                "maintenance_message": current_app.config.get(
                    'MAINTENANCE_MESSAGE',
                    "We are currently performing scheduled maintenance. Please check back later."
                )
            }
            
            # Update status in database
            return self.update_status(status_data)
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return False
    
    def set_maintenance_mode(self, enabled, message=None):
        """
        Set maintenance mode.
        
        Args:
            enabled (bool): Whether maintenance mode is enabled
            message (str, optional): Maintenance message
            
        Returns:
            bool: True if maintenance mode was set, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            # Get current status
            status = self.get_current_status()
            
            if not status:
                # Create new status if none exists
                status = {
                    "_id": "current_status",
                    "timestamp": datetime.utcnow(),
                    "status": "Healthy",
                    "maintenance_mode": enabled
                }
            else:
                # Update existing status
                status["maintenance_mode"] = enabled
                status["timestamp"] = datetime.utcnow()
            
            # Update maintenance message if provided
            if message:
                status["maintenance_message"] = message
            
            # Also update application config
            current_app.config['MAINTENANCE_MODE'] = enabled
            if message:
                current_app.config['MAINTENANCE_MESSAGE'] = message
            
            # Update status in database
            return self.update_status(status)
        except Exception as e:
            logger.error(f"Failed to set maintenance mode: {e}")
            return False
