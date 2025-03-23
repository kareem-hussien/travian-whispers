"""
Scheduled Jobs module for Travian Whispers application.
This module handles scheduled maintenance tasks such as IP rotation and session cleanup.
"""
import logging
import threading
import time
from datetime import datetime, timedelta

from startup.ip_manager import IPManager
from startup.session_isolation import BrowserIsolationManager

# Configure logger
logger = logging.getLogger(__name__)

class ScheduledJobManager:
    """Manager for scheduled maintenance jobs."""
    
    def __init__(self):
        """Initialize ScheduledJobManager."""
        self.ip_manager = IPManager()
        self.browser_manager = BrowserIsolationManager()
        self.stop_event = threading.Event()
        self.maintenance_thread = None
        self.jobs = []
        
        # Define default jobs
        self._setup_default_jobs()
    
    def _setup_default_jobs(self):
        """Setup default maintenance jobs."""
        # IP rotation job (every 12 hours)
        self.jobs.append({
            "name": "ip_rotation",
            "function": self._rotate_ips,
            "interval": 12 * 60 * 60,  # 12 hours
            "last_run": None
        })
        
        # Session cleanup job (every 24 hours)
        self.jobs.append({
            "name": "session_cleanup",
            "function": self._cleanup_sessions,
            "interval": 24 * 60 * 60,  # 24 hours
            "last_run": None
        })
        
        # IP health check job (every 6 hours)
        self.jobs.append({
            "name": "ip_health_check",
            "function": self._check_ip_health,
            "interval": 6 * 60 * 60,  # 6 hours
            "last_run": None
        })
    
    def start(self):
        """Start the scheduled job manager."""
        if self.maintenance_thread and self.maintenance_thread.is_alive():
            logger.warning("Scheduled job manager is already running")
            return False
        
        # Clear stop event
        self.stop_event.clear()
        
        # Start maintenance thread
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop)
        self.maintenance_thread.daemon = True
        self.maintenance_thread.start()
        
        logger.info("Scheduled job manager started")
        return True
    
    def stop(self):
        """Stop the scheduled job manager."""
        if not self.maintenance_thread or not self.maintenance_thread.is_alive():
            logger.warning("Scheduled job manager is not running")
            return False
        
        # Set stop event
        self.stop_event.set()
        
        # Wait for maintenance thread to finish
        self.maintenance_thread.join(timeout=60)
        
        if self.maintenance_thread.is_alive():
            logger.warning("Maintenance thread did not stop gracefully")
        
        logger.info("Scheduled job manager stopped")
        return True
    
    def _maintenance_loop(self):
        """
        Main maintenance loop.
        This runs in a separate thread and executes scheduled jobs.
        """
        logger.info("Maintenance loop started")
        
        while not self.stop_event.is_set():
            try:
                # Check if any jobs need to run
                now = datetime.utcnow()
                
                for job in self.jobs:
                    # Skip if job has been run recently
                    if job["last_run"] and (now - job["last_run"]).total_seconds() < job["interval"]:
                        continue
                    
                    # Run job
                    logger.info(f"Running scheduled job: {job['name']}")
                    try:
                        result = job["function"]()
                        job["last_run"] = now
                        logger.info(f"Job {job['name']} completed: {result}")
                    except Exception as e:
                        logger.error(f"Error in job {job['name']}: {e}")
                
                # Sleep for a while (check every minute)
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                time.sleep(60)
        
        logger.info("Maintenance loop stopped")
    
    def _rotate_ips(self):
        """
        Rotate IPs that have been used for too long.
        
        Returns:
            dict: Job result
        """
        # Define maximum age (12 hours)
        max_age_hours = 12
        
        # Rotate IPs
        rotated_count = self.ip_manager.schedule_ip_rotation(max_age_hours)
        
        return {
            "rotated_count": rotated_count,
            "max_age_hours": max_age_hours
        }
    
    def _cleanup_sessions(self):
        """
        Clean up old browser sessions.
        
        Returns:
            dict: Job result
        """
        # Define maximum age (24 hours)
        max_age_hours = 24
        
        # Clean up sessions
        cleaned_count = self.browser_manager.session_manager.clean_old_sessions(max_age_hours)
        
        return {
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours
        }
    
    def _check_ip_health(self):
        """
        Check health of IPs in the pool.
        
        Returns:
            dict: Job result
        """
        # This would typically involve testing IPs for connectivity and validity
        # For now, we'll just return a placeholder
        
        # Get all IPs
        all_ips = list(self.ip_manager.ip_collection.find())
        
        # Count by status
        status_counts = {}
        for ip in all_ips:
            status = ip.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count in-use IPs
        in_use_count = sum(1 for ip in all_ips if ip.get("inUse", False))
        
        return {
            "total_ips": len(all_ips),
            "in_use": in_use_count,
            "status_counts": status_counts
        }
    
    def add_job(self, name, function, interval_hours):
        """
        Add a custom job to the scheduler.
        
        Args:
            name (str): Job name
            function (callable): Function to execute
            interval_hours (float): Interval in hours
            
        Returns:
            bool: True if job was added, False otherwise
        """
        # Check if job already exists
        for job in self.jobs:
            if job["name"] == name:
                logger.warning(f"Job {name} already exists")
                return False
        
        # Add job
        self.jobs.append({
            "name": name,
            "function": function,
            "interval": interval_hours * 60 * 60,
            "last_run": None
        })
        
        logger.info(f"Added job {name} with interval {interval_hours} hours")
        
        return True
    
    def remove_job(self, name):
        """
        Remove a job from the scheduler.
        
        Args:
            name (str): Job name
            
        Returns:
            bool: True if job was removed, False otherwise
        """
        # Find job
        for i, job in enumerate(self.jobs):
            if job["name"] == name:
                # Remove job
                self.jobs.pop(i)
                logger.info(f"Removed job {name}")
                return True
        
        logger.warning(f"Job {name} not found")
        return False

# Create a singleton instance
scheduled_job_manager = ScheduledJobManager()
