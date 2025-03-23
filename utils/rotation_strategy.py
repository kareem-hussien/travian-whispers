"""
IP Rotation Strategy for Travian Whispers application.
This module provides enhanced rotation strategies based on user activity patterns.
"""
import logging
import random
from datetime import datetime, timedelta
from flask import current_app
from database.models.ip_pool import IPAddress
from database.models.user_activity import UserActivity
from startup.ip_manager import IPManager

# Initialize logger
logger = logging.getLogger(__name__)


class RotationStrategy:
    """Implements different IP rotation strategies based on usage patterns."""
    
    # Rotation strategies
    STRATEGY_TIME_BASED = 'time_based'         # Rotate based on time intervals
    STRATEGY_ACTIVITY_BASED = 'activity_based' # Rotate based on activity volume
    STRATEGY_PATTERN_BASED = 'pattern_based'   # Rotate based on usage patterns
    STRATEGY_RANDOM = 'random'                 # Randomized rotation
    
    def __init__(self):
        """Initialize RotationStrategy."""
        self.ip_manager = IPManager()
        self.activity_model = UserActivity()
    
    def apply_rotation_strategy(self, strategy_type=STRATEGY_TIME_BASED):
        """
        Apply a specific rotation strategy to all active IPs.
        
        Args:
            strategy_type (str): Strategy type to apply
            
        Returns:
            int: Number of IPs rotated
        """
        if strategy_type == self.STRATEGY_TIME_BASED:
            return self._apply_time_based_rotation()
        elif strategy_type == self.STRATEGY_ACTIVITY_BASED:
            return self._apply_activity_based_rotation()
        elif strategy_type == self.STRATEGY_PATTERN_BASED:
            return self._apply_pattern_based_rotation()
        elif strategy_type == self.STRATEGY_RANDOM:
            return self._apply_random_rotation()
        else:
            logger.warning(f"Unknown rotation strategy: {strategy_type}")
            return 0
    
    def _apply_time_based_rotation(self):
        """
        Rotate IPs based on time intervals.
        
        Returns:
            int: Number of IPs rotated
        """
        ip_pool = IPAddress()
        rotation_count = 0
        
        # Get rotation interval from settings
        rotation_interval = current_app.config.get('IP_ROTATION_INTERVAL', 30)  # minutes
        rotation_time = datetime.utcnow() - timedelta(minutes=rotation_interval)
        
        # Get IPs that need rotation
        ips_to_rotate = ip_pool.list_ips(status=IPAddress.STATUS_IN_USE)
        
        for ip in ips_to_rotate:
            # Skip recently rotated IPs
            if ip.get('last_rotation') and ip['last_rotation'] > rotation_time:
                continue
            
            # Rotate the IP
            ip_id = str(ip['_id'])
            logger.info(f"Time-based rotation for IP {ip['ip_address']} (ID: {ip_id})")
            
            if ip_pool.rotate_ip(ip_id):
                rotation_count += 1
        
        logger.info(f"Time-based rotation completed: {rotation_count} IPs rotated")
        return rotation_count
    
    def _apply_activity_based_rotation(self):
        """
        Rotate IPs based on activity volume.
        
        Returns:
            int: Number of IPs rotated
        """
        ip_pool = IPAddress()
        rotation_count = 0
        
        # Define activity thresholds
        high_activity_threshold = current_app.config.get('IP_HIGH_ACTIVITY_THRESHOLD', 100)
        
        # Get IPs in use
        ips_in_use = ip_pool.list_ips(status=IPAddress.STATUS_IN_USE)
        
        for ip in ips_in_use:
            ip_id = str(ip['_id'])
            
            # Get activity counts for users assigned to this IP
            total_activity_count = 0
            
            for user_id in ip.get('assigned_users', []):
                # Get activity count in the last hour
                activity_count = self.activity_model.count_user_activity(
                    user_id, 
                    since=datetime.utcnow() - timedelta(hours=1)
                )
                
                total_activity_count += activity_count
            
            # Rotate if activity exceeds threshold
            if total_activity_count > high_activity_threshold:
                logger.info(f"Activity-based rotation for IP {ip['ip_address']} (ID: {ip_id})")
                logger.info(f"Activity count: {total_activity_count} (threshold: {high_activity_threshold})")
                
                if ip_pool.rotate_ip(ip_id):
                    rotation_count += 1
        
        logger.info(f"Activity-based rotation completed: {rotation_count} IPs rotated")
        return rotation_count
    
    def _apply_pattern_based_rotation(self):
        """
        Rotate IPs based on usage patterns to avoid detection.
        
        Returns:
            int: Number of IPs rotated
        """
        ip_pool = IPAddress()
        rotation_count = 0
        
        # Get IPs in use
        ips_in_use = ip_pool.list_ips(status=IPAddress.STATUS_IN_USE)
        
        for ip in ips_in_use:
            ip_id = str(ip['_id'])
            
            # Skip IPs with no assigned users
            if not ip.get('assigned_users'):
                continue
            
            # Calculate risk score based on usage patterns
            risk_score = self._calculate_pattern_risk(ip)
            
            # Rotate if risk score is high
            if risk_score > 70:  # 70% risk threshold
                logger.info(f"Pattern-based rotation for IP {ip['ip_address']} (ID: {ip_id})")
                logger.info(f"Risk score: {risk_score}%")
                
                if ip_pool.rotate_ip(ip_id):
                    rotation_count += 1
        
        logger.info(f"Pattern-based rotation completed: {rotation_count} IPs rotated")
        return rotation_count
    
    def _calculate_pattern_risk(self, ip_data):
        """
        Calculate detection risk based on usage patterns.
        
        Args:
            ip_data (dict): IP data including assigned users
            
        Returns:
            float: Risk score (0-100)
        """
        risk_score = 0
        
        # Factor 1: Number of users sharing the IP
        user_count = len(ip_data.get('assigned_users', []))
        if user_count > 1:
            risk_score += min(user_count * 10, 50)  # Max 50 points for this factor
        
        # Factor 2: Time in use
        if ip_data.get('last_rotation'):
            hours_in_use = (datetime.utcnow() - ip_data['last_rotation']).total_seconds() / 3600
            risk_score += min(hours_in_use * 2, 30)  # Max 30 points for this factor
        
        # Factor 3: Randomization factor (to avoid predictable patterns)
        risk_score += random.randint(0, 20)  # Random component max 20 points
        
        # Cap at 100
        return min(risk_score, 100)
    
    def _apply_random_rotation(self):
        """
        Apply random rotation to avoid predictable patterns.
        
        Returns:
            int: Number of IPs rotated
        """
        ip_pool = IPAddress()
        rotation_count = 0
        
        # Get IPs in use
        ips_in_use = ip_pool.list_ips(status=IPAddress.STATUS_IN_USE)
        
        # Randomly select IPs to rotate (25% chance)
        for ip in ips_in_use:
            if random.random() < 0.25:  # 25% chance to rotate
                ip_id = str(ip['_id'])
                logger.info(f"Random rotation for IP {ip['ip_address']} (ID: {ip_id})")
                
                if ip_pool.rotate_ip(ip_id):
                    rotation_count += 1
        
        logger.info(f"Random rotation completed: {rotation_count} IPs rotated")
        return rotation_count
    
    def recommend_strategy_for_user(self, user_id):
        """
        Recommend a rotation strategy based on user profile.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            str: Recommended strategy type
        """
        # Get user data
        from database.models.user import User
        user_model = User()
        user = user_model.get_user_by_id(user_id)
        
        if not user:
            return self.STRATEGY_TIME_BASED  # Default
        
        # Check if premium user
        is_premium = False
        if 'subscription' in user and 'planId' in user['subscription']:
            from database.models.subscription import SubscriptionPlan
            plan_model = SubscriptionPlan()
            plan = plan_model.get_plan_by_id(user['subscription']['planId'])
            
            if plan and plan['name'] == 'Premium':
                is_premium = True
        
        # Check activity level
        activity_count = self.activity_model.count_user_activity(
            user_id, 
            since=datetime.utcnow() - timedelta(days=7)
        )
        
        high_activity = activity_count > 1000  # Arbitrary threshold
        
        # Recommend strategy based on user profile
        if is_premium and high_activity:
            return self.STRATEGY_PATTERN_BASED
        elif is_premium:
            return self.STRATEGY_ACTIVITY_BASED
        elif high_activity:
            return self.STRATEGY_RANDOM
        else:
            return self.STRATEGY_TIME_BASED