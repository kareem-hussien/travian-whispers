"""
IP Rotation module for Travian Whispers application.
This module provides scheduling and automation for IP rotation strategies.
"""
import logging
import time
import threading
import random
from datetime import datetime, timedelta
from startup.ip_manager import IPManager
from utils.rotation_strategy import RotationStrategy
from config.ip_config import (
    IP_ROTATION_INTERVAL,
    IP_DEFAULT_ROTATION_STRATEGY,
    IP_ROTATION_STRATEGIES
)

# Initialize logger
logger = logging.getLogger(__name__)

class IPRotationScheduler:
    """Scheduler for automatic IP rotation."""
    
    def __init__(self):
        """Initialize IPRotationScheduler."""
        self.ip_manager = IPManager()
        self.rotation_strategy = RotationStrategy()
        self.stop_event = threading.Event()
        self.scheduler_thread = None
        self.rotation_schedules = {}
        self.last_global_rotation = datetime.utcnow()
    
    def start(self):
        """Start the IP rotation scheduler."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("IP rotation scheduler is already running")
            return False
        
        # Clear stop event
        self.stop_event.clear()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("IP rotation scheduler started")
        return True
    
    def stop(self):
        """Stop the IP rotation scheduler."""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            logger.warning("IP rotation scheduler is not running")
            return False
        
        # Set stop event
        self.stop_event.set()
        
        # Wait for scheduler thread to finish
        self.scheduler_thread.join(timeout=60)
        
        if self.scheduler_thread.is_alive():
            logger.warning("Scheduler thread did not stop gracefully")
        
        logger.info("IP rotation scheduler stopped")
        return True
    
    def _scheduler_loop(self):
        """
        Main scheduler loop.
        This runs in a separate thread and performs scheduled rotations.
        """
        logger.info("IP rotation scheduler loop started")
        
        while not self.stop_event.is_set():
            try:
                now = datetime.utcnow()
                
                # Check for global rotation
                global_rotation_interval = timedelta(hours=12)  # Default global rotation interval
                if now - self.last_global_rotation > global_rotation_interval:
                    self._perform_global_rotation()
                    self.last_global_rotation = now
                
                # Check individual user rotation schedules
                self._check_user_schedules(now)
                
                # Sleep for a while (check every minute)
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in IP rotation scheduler loop: {e}")
                time.sleep(60)
        
        logger.info("IP rotation scheduler loop stopped")
    
    def _perform_global_rotation(self):
        """Perform a global rotation using the configured strategy."""
        try:
            strategy = IP_DEFAULT_ROTATION_STRATEGY
            logger.info(f"Performing global IP rotation using {strategy} strategy")
            
            rotated_count = self.rotation_strategy.apply_rotation_strategy(strategy)
            
            logger.info(f"Global rotation completed: {rotated_count} IPs rotated")
        except Exception as e:
            logger.error(f"Error performing global rotation: {e}")
    
    def _check_user_schedules(self, now):
        """
        Check individual user rotation schedules.
        
        Args:
            now (datetime): Current UTC time
        """
        # Copy dictionary to avoid modification during iteration
        schedules = self.rotation_schedules.copy()
        
        for user_id, schedule in schedules.items():
            if now >= schedule["next_rotation"]:
                try:
                    # Rotate IP for user
                    logger.info(f"Scheduled rotation for user {user_id}")
                    new_ip = self.ip_manager.rotate_ip_for_user(user_id)
                    
                    if new_ip:
                        logger.info(f"Rotated IP for user {user_id} to {new_ip['ip']}")
                    else:
                        logger.warning(f"Failed to rotate IP for user {user_id}")
                    
                    # Update next rotation time based on interval and randomization
                    interval_seconds = schedule["interval"]
                    randomization = schedule.get("randomize", 0)  # Randomize in minutes
                    
                    if randomization > 0:
                        # Add randomization within range (convert to seconds)
                        interval_seconds += random.randint(-randomization, randomization) * 60
                    
                    # Ensure minimum interval of 10 minutes
                    interval_seconds = max(interval_seconds, 600)
                    
                    # Update next rotation time
                    schedule["next_rotation"] = now + timedelta(seconds=interval_seconds)
                    schedule["last_rotation"] = now
                    
                    # If schedule is temporary, check if it should be removed
                    if schedule.get("temporary", False):
                        schedule["rotations_left"] -= 1
                        if schedule["rotations_left"] <= 0:
                            self.rotation_schedules.pop(user_id, None)
                            logger.info(f"Removed temporary rotation schedule for user {user_id}")
                    
                except Exception as e:
                    logger.error(f"Error rotating IP for user {user_id}: {e}")
    
    def schedule_user_rotation(self, user_id, interval_minutes=None, strategy=None, randomize=0, start_now=False):
        """
        Schedule regular IP rotation for a user.
        
        Args:
            user_id (str): User ID
            interval_minutes (int, optional): Rotation interval in minutes
            strategy (str, optional): Rotation strategy to use
            randomize (int, optional): Randomization in minutes (+/-)
            start_now (bool, optional): Whether to perform an immediate rotation
            
        Returns:
            dict: Rotation schedule details
        """
        # Use default interval if not specified
        if interval_minutes is None:
            interval_minutes = IP_ROTATION_INTERVAL
        
        # Use default strategy if not specified
        if strategy is None:
            strategy = IP_DEFAULT_ROTATION_STRATEGY
        
        # Validate strategy
        if strategy not in IP_ROTATION_STRATEGIES:
            logger.warning(f"Unknown rotation strategy: {strategy}, using default")
            strategy = IP_DEFAULT_ROTATION_STRATEGY
        
        # Calculate first rotation time
        next_rotation = datetime.utcnow()
        if not start_now:
            next_rotation += timedelta(minutes=interval_minutes)
            
            # Add randomization if specified
            if randomize > 0:
                next_rotation += timedelta(minutes=random.randint(-randomize, randomize))
        
        # Create schedule
        schedule = {
            "interval": interval_minutes * 60,  # Convert to seconds
            "strategy": strategy,
            "randomize": randomize,
            "next_rotation": next_rotation,
            "last_rotation": None,
            "temporary": False
        }
        
        # Store schedule
        self.rotation_schedules[user_id] = schedule
        
        logger.info(f"Scheduled IP rotation for user {user_id} every {interval_minutes} minutes using {strategy} strategy")
        
        # Perform immediate rotation if requested
        if start_now:
            try:
                new_ip = self.ip_manager.rotate_ip_for_user(user_id)
                
                if new_ip:
                    logger.info(f"Immediate rotation for user {user_id} to IP {new_ip['ip']}")
                    schedule["last_rotation"] = datetime.utcnow()
                else:
                    logger.warning(f"Failed to perform immediate rotation for user {user_id}")
            except Exception as e:
                logger.error(f"Error performing immediate rotation for user {user_id}: {e}")
        
        return schedule
    
    def schedule_temporary_rotation(self, user_id, count=3, interval_minutes=10, start_now=True):
        """
        Schedule temporary IP rotations for a user.
        Useful for recovery from detection or suspicious activity.
        
        Args:
            user_id (str): User ID
            count (int, optional): Number of rotations to perform
            interval_minutes (int, optional): Interval between rotations
            start_now (bool, optional): Whether to perform an immediate rotation
            
        Returns:
            dict: Rotation schedule details
        """
        # Calculate first rotation time
        next_rotation = datetime.utcnow()
        if not start_now:
            next_rotation += timedelta(minutes=interval_minutes)
        
        # Create schedule
        schedule = {
            "interval": interval_minutes * 60,  # Convert to seconds
            "strategy": IP_DEFAULT_ROTATION_STRATEGY,
            "randomize": 0,  # No randomization for recovery
            "next_rotation": next_rotation,
            "last_rotation": None,
            "temporary": True,
            "rotations_left": count
        }
        
        # Store schedule (overwrite any existing schedule)
        self.rotation_schedules[user_id] = schedule
        
        logger.info(f"Scheduled temporary IP rotation for user {user_id}: {count} rotations every {interval_minutes} minutes")
        
        # Perform immediate rotation if requested
        if start_now:
            try:
                new_ip = self.ip_manager.rotate_ip_for_user(user_id)
                
                if new_ip:
                    logger.info(f"Immediate rotation for user {user_id} to IP {new_ip['ip']}")
                    schedule["last_rotation"] = datetime.utcnow()
                    # Decrement rotations left since we've done one
                    schedule["rotations_left"] -= 1
                    if schedule["rotations_left"] <= 0:
                        self.rotation_schedules.pop(user_id, None)
                        logger.info(f"Removed temporary rotation schedule for user {user_id} (completed)")
                else:
                    logger.warning(f"Failed to perform immediate rotation for user {user_id}")
            except Exception as e:
                logger.error(f"Error performing immediate rotation for user {user_id}: {e}")
        
        return schedule
    
    def unschedule_user_rotation(self, user_id):
        """
        Remove scheduled rotation for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if schedule was removed, False if not found
        """
        if user_id in self.rotation_schedules:
            self.rotation_schedules.pop(user_id)
            logger.info(f"Removed rotation schedule for user {user_id}")
            return True
        else:
            logger.warning(f"No rotation schedule found for user {user_id}")
            return False
    
    def get_rotation_schedule(self, user_id):
        """
        Get the current rotation schedule for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Rotation schedule or None if not found
        """
        return self.rotation_schedules.get(user_id)
    
    def recommend_rotation_schedule(self, user_id):
        """
        Recommend a rotation schedule based on user activity patterns.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Recommended rotation schedule
        """
        # Get recommended strategy
        strategy = self.rotation_strategy.recommend_strategy_for_user(user_id)
        
        # Get user data from database
        try:
            from database.models.user import User
            user_model = User()
            user = user_model.get_user_by_id(user_id)
            
            # Default schedule
            schedule = {
                "interval_minutes": IP_ROTATION_INTERVAL,
                "strategy": strategy,
                "randomize": 10,  # Default randomization
                "reason": "Default schedule"
            }
            
            if user:
                # Customize based on subscription plan
                if user.get('subscription') and user['subscription'].get('planId'):
                    from database.models.subscription import SubscriptionPlan
                    plan_model = SubscriptionPlan()
                    plan = plan_model.get_plan_by_id(user['subscription']['planId'])
                    
                    if plan:
                        plan_name = plan.get('name', '').lower()
                        
                        if plan_name == 'premium':
                            # Premium users get more frequent rotation and higher randomization
                            schedule["interval_minutes"] = 20
                            schedule["randomize"] = 15
                            schedule["reason"] = "Premium subscription plan"
                        elif plan_name == 'standard':
                            # Standard users get default rotation with higher randomization
                            schedule["interval_minutes"] = IP_ROTATION_INTERVAL
                            schedule["randomize"] = 12
                            schedule["reason"] = "Standard subscription plan"
                
                # Check activity level to adjust schedule
                from database.models.user_activity import UserActivity
                activity_model = UserActivity()
                
                # Count recent activity
                recent_activity = activity_model.count_user_activity(
                    user_id, 
                    since=datetime.utcnow() - timedelta(days=1)
                )
                
                if recent_activity > 1000:
                    # Very active users need more frequent rotation
                    schedule["interval_minutes"] = min(schedule["interval_minutes"], 15)
                    schedule["reason"] = "High activity user"
                elif recent_activity < 100:
                    # Less active users can have less frequent rotation
                    schedule["interval_minutes"] = 60
                    schedule["reason"] = "Low activity user"
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error recommending rotation schedule: {e}")
            
            # Return default schedule on error
            return {
                "interval_minutes": IP_ROTATION_INTERVAL,
                "strategy": IP_DEFAULT_ROTATION_STRATEGY,
                "randomize": 10,
                "reason": "Default schedule (error occurred)"
            }

# Create a singleton instance
ip_rotation_scheduler = IPRotationScheduler()
