"""
IP Manager for Travian Whispers application.
This module provides the IP manager for allocation and rotation.
"""
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from flask import current_app
from database.models.ip_pool import IPAddress
from database.models.proxy_service import ProxyService
from database.settings import Settings

# Initialize logger
logger = logging.getLogger(__name__)


class IPManager:
    """IP Manager for handling IP allocation and rotation."""
    
    # Singleton instance
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(IPManager, cls).__new__(cls)
                cls._instance.ip_pool = IPAddress()
                cls._instance.proxy_service = ProxyService()
                cls._instance.settings = Settings()
                cls._instance.rotation_thread = None
                cls._instance.running = False
                cls._instance.user_ip_cache = {}
                cls._instance.stagger_thread = None
                
        return cls._instance
    
    def initialize(self):
        """Initialize the IP manager."""
        logger.info("Initializing IP Manager")
        
        # Load settings
        self.load_settings()
        
        # Create indexes
        self.ip_pool.create_indexes()
        self.proxy_service.create_indexes()
        
        # Start rotation thread if configured
        if self.auto_rotation:
            self.start_rotation_thread()
            
        # Start stagger thread
        self.start_stagger_thread()
        
        logger.info("IP Manager initialized")
    
    def load_settings(self):
        """Load IP management settings."""
        # Default settings
        self.auto_rotation = True
        self.rotation_interval = 30  # minutes
        self.cooldown_period = 15    # minutes
        self.max_failures = 5
        self.max_ban_count = 3
        self.ip_fetch_threshold = 20
        
        # Get settings from database
        settings = self.settings.get_all_settings()
        
        # Override defaults with database settings
        self.auto_rotation = settings.get('ip_auto_rotation', True)
        self.rotation_interval = int(settings.get('ip_rotation_interval', 30))
        self.cooldown_period = int(settings.get('ip_cooldown_period', 15))
        self.max_failures = int(settings.get('ip_max_failures', 5))
        self.max_ban_count = int(settings.get('ip_max_ban_count', 3))
        self.ip_fetch_threshold = int(settings.get('ip_fetch_threshold', 20))
        
        # Apply settings to Flask app config
        current_app.config['IP_COOLDOWN_MINUTES'] = self.cooldown_period
        current_app.config['IP_FAILURE_THRESHOLD'] = self.max_failures
        
        logger.info(f"Loaded IP Manager settings: "
                   f"auto_rotation={self.auto_rotation}, "
                   f"rotation_interval={self.rotation_interval}m, "
                   f"cooldown_period={self.cooldown_period}m")
    
    def get_ip_for_user(self, user_id, country_code=None, ip_type=None, force_new=False):
        """
        Get an IP for a user, either from cache or by assigning a new one.
        
        Args:
            user_id (str): The user ID
            country_code (str, optional): Preferred country
            ip_type (str, optional): Preferred IP type
            force_new (bool, optional): Force a new IP assignment
            
        Returns:
            dict: IP details or None if no IP available
        """
        # Check if user already has an assigned IP
        if not force_new and user_id in self.user_ip_cache:
            cached_ip = self.user_ip_cache[user_id]
            
            # Verify the IP is still valid and assigned to the user
            ip = self.ip_pool.get_ip(cached_ip['_id'])
            
            if ip and ip['status'] == IPAddress.STATUS_IN_USE and user_id in ip['assigned_users']:
                logger.debug(f"Using cached IP {ip['ip_address']} for user {user_id}")
                return ip
            else:
                # Invalid cache, remove it
                logger.debug(f"Cached IP for user {user_id} is no longer valid, assigning new IP")
                self.user_ip_cache.pop(user_id, None)
        
        # Assign a new IP
        ip = self.ip_pool.assign_ip_to_user(user_id, country_code=country_code, ip_type=ip_type)
        
        if ip:
            # Add to cache
            self.user_ip_cache[user_id] = ip
            logger.info(f"Assigned IP {ip['ip_address']} to user {user_id}")
            return ip
        else:
            # No IPs available, try to fetch more
            logger.warning(f"No available IPs for user {user_id}, attempting to fetch more")
            self.proxy_service.auto_fetch_proxies(min_available=self.ip_fetch_threshold)
            
            # Try again
            ip = self.ip_pool.assign_ip_to_user(user_id, country_code=country_code, ip_type=ip_type)
            
            if ip:
                self.user_ip_cache[user_id] = ip
                logger.info(f"Assigned newly fetched IP {ip['ip_address']} to user {user_id}")
                return ip
            else:
                logger.error(f"Failed to assign IP to user {user_id} after fetch attempt")
                return None
    
    def release_ip_for_user(self, user_id, ip_id=None):
        """
        Release an IP assigned to a user.
        
        Args:
            user_id (str): The user ID
            ip_id (str, optional): Specific IP ID to release, or all if None
            
        Returns:
            bool: True if released, False otherwise
        """
        if ip_id:
            # Release specific IP
            success = self.ip_pool.unassign_ip_from_user(user_id, ip_id)
            
            if success:
                # Remove from cache if it matches
                if user_id in self.user_ip_cache and str(self.user_ip_cache[user_id]['_id']) == ip_id:
                    self.user_ip_cache.pop(user_id, None)
                    
                logger.info(f"Released IP {ip_id} for user {user_id}")
                return True
            else:
                logger.warning(f"Failed to release IP {ip_id} for user {user_id}")
                return False
        else:
            # Release all IPs for user
            ips = self.ip_pool.get_user_ips(user_id)
            success = True
            
            for ip in ips:
                ip_success = self.ip_pool.unassign_ip_from_user(user_id, str(ip['_id']))
                if not ip_success:
                    success = False
            
            # Remove from cache regardless
            if user_id in self.user_ip_cache:
                self.user_ip_cache.pop(user_id, None)
                
            if success:
                logger.info(f"Released all IPs for user {user_id}")
            else:
                logger.warning(f"Failed to release some IPs for user {user_id}")
                
            return success
    
    def rotate_ip_for_user(self, user_id):
        """
        Rotate the IP for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            dict: New IP details or None if failed
        """
        # Get current IP
        current_ip = None
        if user_id in self.user_ip_cache:
            current_ip = self.user_ip_cache[user_id]
        
        # Release current IP
        if current_ip:
            self.release_ip_for_user(user_id, str(current_ip['_id']))
        
        # Get user from database to determine preferences
        from database.models.user import User
        user_model = User()
        user = user_model.get_user_by_id(user_id)
        
        country_code = None
        ip_type = None
        
        if user:
            # Extract preferences from user data if available
            # This is placeholder - actual implementation would depend on user schema
            if 'settings' in user and 'ip_preferences' in user['settings']:
                country_code = user['settings']['ip_preferences'].get('country_code')
                ip_type = user['settings']['ip_preferences'].get('ip_type')
        
        # Get new IP
        return self.get_ip_for_user(user_id, country_code=country_code, ip_type=ip_type, force_new=True)
    
    def report_ip_failure(self, ip_id, failure_type, details=None):
        """
        Report an IP failure.
        
        Args:
            ip_id (str): The IP ID
            failure_type (str): Type of failure
            details (str, optional): Additional details
            
        Returns:
            bool: True if reported, False otherwise
        """
        success = self.ip_pool.report_ip_failure(ip_id, failure_type, details)
        
        if success:
            logger.info(f"Reported failure for IP {ip_id}: {failure_type}")
            
            # Get updated IP to check failure count
            ip = self.ip_pool.get_ip(ip_id)
            
            if ip and ip['failure_count'] >= self.max_failures:
                logger.warning(f"IP {ip['ip_address']} has reached failure threshold, flagging")
                self.ip_pool.update_ip_status(ip_id, IPAddress.STATUS_FLAGGED, 
                                           f"Exceeded failure threshold: {ip['failure_count']}")
            
            return True
        else:
            logger.warning(f"Failed to report failure for IP {ip_id}")
            return False
    
    def report_ip_ban(self, ip_id, reason=None):
        """
        Report an IP as banned.
        
        Args:
            ip_id (str): The IP ID
            reason (str, optional): Ban reason
            
        Returns:
            bool: True if reported, False otherwise
        """
        success = self.ip_pool.update_ip_status(ip_id, IPAddress.STATUS_BANNED, reason)
        
        if success:
            logger.warning(f"Reported IP {ip_id} as banned: {reason}")
            
            # Get updated IP to check ban count
            ip = self.ip_pool.get_ip(ip_id)
            
            if ip and ip['ban_count'] >= self.max_ban_count:
                logger.warning(f"IP {ip['ip_address']} has been banned {ip['ban_count']} times, removing from pool")
                self.ip_pool.remove_ip(ip_id)
            
            return True
        else:
            logger.warning(f"Failed to report ban for IP {ip_id}")
            return False
    
    def start_rotation_thread(self):
        """Start the automatic IP rotation thread."""
        if self.rotation_thread and self.rotation_thread.is_alive():
            logger.warning("IP rotation thread already running")
            return
            
        self.running = True
        self.rotation_thread = threading.Thread(target=self._rotation_worker, daemon=True)
        self.rotation_thread.start()
        logger.info("Started IP rotation thread")
    
    def stop_rotation_thread(self):
        """Stop the automatic IP rotation thread."""
        self.running = False
        
        if self.rotation_thread:
            self.rotation_thread.join(timeout=5)
            logger.info("Stopped IP rotation thread")
    
    def _rotation_worker(self):
        """Worker function for the IP rotation thread."""
        logger.info("IP rotation worker thread started")
        
        while self.running:
            try:
                # Refresh settings first
                self.load_settings()
                
                # Get IPs that need rotation
                rotation_time = datetime.utcnow() - timedelta(minutes=self.rotation_interval)
                ips_to_rotate = self.ip_pool.list_ips(status=IPAddress.STATUS_IN_USE)
                
                for ip in ips_to_rotate:
                    # Skip recently rotated IPs
                    if ip.get('last_rotation') and ip['last_rotation'] > rotation_time:
                        continue
                    
                    # Rotate the IP
                    ip_id = str(ip['_id'])
                    logger.info(f"Auto-rotating IP {ip['ip_address']} (ID: {ip_id})")
                    
                    # Get users assigned to this IP
                    users = ip.get('assigned_users', [])
                    
                    # Rotate the IP
                    self.ip_pool.rotate_ip(ip_id)
                    
                    # Assign new IPs to affected users
                    for user_id in users:
                        # Remove from cache
                        if user_id in self.user_ip_cache:
                            self.user_ip_cache.pop(user_id, None)
                            
                        # This will happen when the user next accesses the system
                        logger.info(f"User {user_id} will be assigned a new IP on next request")
                
                # Make cooldown IPs available if cooldown period has elapsed
                cooldown_time = datetime.utcnow() - timedelta(minutes=self.cooldown_period)
                cooldown_ips = self.ip_pool.list_ips(status=IPAddress.STATUS_COOLDOWN)
                
                for ip in cooldown_ips:
                    if ip.get('last_rotation') and ip['last_rotation'] < cooldown_time:
                        self.ip_pool.update_ip_status(str(ip['_id']), IPAddress.STATUS_AVAILABLE,
                                                   "Automatic availability after cooldown")
                        logger.info(f"IP {ip['ip_address']} is now available after cooldown")
                
                # Check if we need to fetch more IPs
                available_ips = self.ip_pool.list_ips(status=IPAddress.STATUS_AVAILABLE)
                
                if len(available_ips) < self.ip_fetch_threshold:
                    logger.info(f"Available IPs ({len(available_ips)}) below threshold ({self.ip_fetch_threshold}), fetching more")
                    self.proxy_service.auto_fetch_proxies(min_available=self.ip_fetch_threshold)
                
                # Sleep for a while before the next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in IP rotation worker: {e}")
                time.sleep(60)  # Sleep and retry on error
        
        logger.info("IP rotation worker thread stopped")
    
    def start_stagger_thread(self):
        """Start the user activity staggering thread."""
        if self.stagger_thread and self.stagger_thread.is_alive():
            logger.warning("Stagger thread already running")
            return
            
        self.running = True
        self.stagger_thread = threading.Thread(target=self._stagger_worker, daemon=True)
        self.stagger_thread.start()
        logger.info("Started user activity staggering thread")
    
    def stop_stagger_thread(self):
        """Stop the user activity staggering thread."""
        self.running = False
        
        if self.stagger_thread:
            self.stagger_thread.join(timeout=5)
            logger.info("Stopped user activity staggering thread")
    
    def _stagger_worker(self):
        """Worker function for the user activity staggering thread."""
        logger.info("User activity staggering worker thread started")
        
        # Dictionary to track last activity for each user
        last_activity = {}
        
        while self.running:
            try:
                # Get active users with tasks
                from database.models.user import User
                from database.models.activity import UserActivity
                
                user_model = User()
                activity_model = UserActivity()
                
                # Get active users (this is a placeholder, actual implementation would depend on your schema)
                active_users = user_model.list_users(subscription_status="active")
                
                # Get users' IP assignments for analysis
                ip_assignments = {}
                
                for user in active_users:
                    user_id = str(user['_id'])
                    user_ips = self.ip_pool.get_user_ips(user_id)
                    
                    for ip in user_ips:
                        ip_id = str(ip['_id'])
                        
                        if ip_id not in ip_assignments:
                            ip_assignments[ip_id] = []
                            
                        ip_assignments[ip_id].append(user_id)
                
                # Identify conflicting users (users sharing the same IP)
                for ip_id, users in ip_assignments.items():
                    if len(users) > 1:
                        logger.info(f"IP {ip_id} has {len(users)} assigned users, staggering activity")
                        
                        # Sort users by last activity time (oldest first)
                        users.sort(key=lambda u: last_activity.get(u, datetime.min))
                        
                        # Stagger user activity by setting cooldowns
                        for i, user_id in enumerate(users):
                            # Set activity cooldown proportional to position in list
                            cooldown = i * 5  # 5 minute stagger per user
                            
                            # Record last activity time for future staggering
                            last_activity[user_id] = datetime.utcnow()
                            
                            logger.info(f"User {user_id} on shared IP {ip_id} scheduled with {cooldown}m cooldown")
                
                # Sleep for a while before the next check
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in stagger worker: {e}")
                time.sleep(300)  # Sleep and retry on error
        
        logger.info("User activity staggering worker thread stopped")
    
    def get_proxy_url(self, ip_data):
        """
        Get a fully formatted proxy URL from IP data.
        
        Args:
            ip_data (dict): IP data
            
        Returns:
            str: Fully formatted proxy URL with auth
        """
        if not ip_data or 'proxy_url' not in ip_data:
            return None
        
        proxy_url = ip_data['proxy_url']
        
        # Check if authentication is required
        if ip_data.get('username') and ip_data.get('password'):
            # Split the proxy URL into components
            if '://' in proxy_url:
                protocol, address = proxy_url.split('://', 1)
            else:
                protocol = 'http'
                address = proxy_url
            
            # Add authentication
            auth_url = f"{protocol}://{ip_data['username']}:{ip_data['password']}@{address}"
            return auth_url
        
        # No auth needed
        return proxy_url
    
    def get_proxy_dict(self, ip_data):
        """
        Get a proxy dictionary for requests library.
        
        Args:
            ip_data (dict): IP data
            
        Returns:
            dict: Proxy dictionary for requests
        """
        if not ip_data or 'proxy_url' not in ip_data:
            return None
        
        proxy_url = self.get_proxy_url(ip_data)
        
        if not proxy_url:
            return None
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def recommend_ip_for_user(self, user_id, user_data=None):
        """
        Recommend the best IP type for a user based on their usage.
        
        Args:
            user_id (str): The user ID
            user_data (dict, optional): User data if available
            
        Returns:
            dict: Recommendation with ip_type and country_code
        """
        # Default recommendation
        recommendation = {
            'ip_type': IPAddress.TYPE_RESIDENTIAL,  # Residential IPs are generally safer
            'country_code': None  # No specific country preference
        }
        
        if not user_data:
            # Get user data
            from database.models.user import User
            user_model = User()
            user_data = user_model.get_user_by_id(user_id)
        
        if not user_data:
            return recommendation
        
        # Look for Travian credentials to determine country
        if 'travianCredentials' in user_data and 'server' in user_data['travianCredentials']:
            server = user_data['travianCredentials']['server']
            
            # Extract country from server URL (e.g., ts1.us.travian.com)
            if server and '.' in server:
                parts = server.split('.')
                for part in parts:
                    if len(part) == 2:  # Two-letter country code
                        recommendation['country_code'] = part.upper()
                        break
        
        # Determine IP type based on subscription level
        if 'subscription' in user_data and 'planId' in user_data['subscription']:
            plan_id = user_data['subscription']['planId']
            
            # Get plan details
            from database.models.subscription import SubscriptionPlan
            plan_model = SubscriptionPlan()
            plan = plan_model.get_plan_by_id(plan_id)
            
            if plan:
                # Higher tier plans get better IPs
                if plan['name'] == 'Premium':
                    recommendation['ip_type'] = IPAddress.TYPE_RESIDENTIAL
                elif plan['name'] == 'Standard':
                    # Mix of residential and datacenter
                    recommendation['ip_type'] = random.choice(
                        [IPAddress.TYPE_RESIDENTIAL, IPAddress.TYPE_DATACENTER]
                    )
                else:
                    # Basic plan gets datacenter IPs
                    recommendation['ip_type'] = IPAddress.TYPE_DATACENTER
        
        return recommendation