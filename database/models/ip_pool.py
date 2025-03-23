"""
IP Pool model for Travian Whispers application.
This module provides the IPPool model for managing and rotating IP addresses.
"""
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class IPAddress:
    """IP Address model for storing IP details and status."""
    
    # IP Status Constants
    STATUS_AVAILABLE = 'available'
    STATUS_IN_USE = 'in_use'
    STATUS_COOLDOWN = 'cooldown'
    STATUS_FLAGGED = 'flagged'
    STATUS_BANNED = 'banned'
    
    # IP Types
    TYPE_DATACENTER = 'datacenter'
    TYPE_RESIDENTIAL = 'residential'
    TYPE_MOBILE = 'mobile'
    TYPE_DEDICATED = 'dedicated'
    
    def __init__(self):
        """Initialize IPAddress model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["ipAddresses"]
            
    def add_ip(self, ip_address, proxy_url=None, username=None, password=None, 
              ip_type=TYPE_DATACENTER, country_code=None, region=None, 
              provider=None, max_users=1):
        """
        Add a new IP address to the pool.
        
        Args:
            ip_address (str): The IP address
            proxy_url (str, optional): Proxy URL if used through a proxy
            username (str, optional): Username for proxy authentication
            password (str, optional): Password for proxy authentication
            ip_type (str, optional): Type of IP (datacenter, residential, etc.)
            country_code (str, optional): Two-letter country code
            region (str, optional): Region or state code
            provider (str, optional): Proxy provider name
            max_users (int, optional): Maximum number of concurrent users
            
        Returns:
            dict: The created IP document or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        # Check if IP already exists
        existing_ip = self.collection.find_one({"ip_address": ip_address})
        if existing_ip:
            logger.warning(f"IP {ip_address} already exists in the pool")
            return existing_ip
            
        ip_data = {
            "ip_address": ip_address,
            "proxy_url": proxy_url,
            "username": username,
            "password": password,
            "ip_type": ip_type,
            "country_code": country_code,
            "region": region,
            "provider": provider,
            "status": self.STATUS_AVAILABLE,
            "max_users": max_users,
            "current_users": 0,
            "assigned_users": [],
            "last_used": None,
            "last_rotation": datetime.utcnow(),
            "failure_count": 0,
            "ban_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = self.collection.insert_one(ip_data)
            if result.inserted_id:
                ip_data["_id"] = result.inserted_id
                logger.info(f"Added new IP {ip_address} to the pool")
                return ip_data
            return None
        except Exception as e:
            logger.error(f"Failed to add IP to pool: {e}")
            return None
    
    def remove_ip(self, ip_id):
        """
        Remove an IP from the pool.
        
        Args:
            ip_id (str): The ID of the IP to remove
            
        Returns:
            bool: True if removed, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            result = self.collection.delete_one({"_id": ObjectId(ip_id)})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Removed IP with ID {ip_id} from pool")
            else:
                logger.warning(f"Failed to remove IP with ID {ip_id}, IP not found")
                
            return success
        except Exception as e:
            logger.error(f"Error removing IP from pool: {e}")
            return False
    
    def update_ip_status(self, ip_id, status, reason=None):
        """
        Update the status of an IP.
        
        Args:
            ip_id (str): The ID of the IP
            status (str): New status
            reason (str, optional): Reason for status change
            
        Returns:
            bool: True if updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if reason:
            update_data["status_reason"] = reason
            
        if status == self.STATUS_BANNED:
            # Increment ban count if being marked as banned
            update_data["$inc"] = {"ban_count": 1}
            
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(ip_id)},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            
            if success:
                logger.info(f"Updated IP {ip_id} status to {status}")
                
                # If banned or flagged, unassign all users
                if status in [self.STATUS_BANNED, self.STATUS_FLAGGED]:
                    self.unassign_all_users(ip_id)
            else:
                logger.warning(f"Failed to update IP {ip_id} status, IP not found")
                
            return success
        except Exception as e:
            logger.error(f"Error updating IP status: {e}")
            return False
    
    def get_ip(self, ip_id):
        """
        Get an IP by ID.
        
        Args:
            ip_id (str): The ID of the IP
            
        Returns:
            dict: IP details or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        try:
            ip = self.collection.find_one({"_id": ObjectId(ip_id)})
            return ip
        except Exception as e:
            logger.error(f"Error getting IP: {e}")
            return None
            
    def get_ip_by_address(self, ip_address):
        """
        Get an IP by its address.
        
        Args:
            ip_address (str): The IP address
            
        Returns:
            dict: IP details or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        try:
            ip = self.collection.find_one({"ip_address": ip_address})
            return ip
        except Exception as e:
            logger.error(f"Error getting IP by address: {e}")
            return None
    
    def list_ips(self, status=None, ip_type=None, country_code=None, provider=None):
        """
        List IPs with optional filtering.
        
        Args:
            status (str, optional): Filter by status
            ip_type (str, optional): Filter by IP type
            country_code (str, optional): Filter by country code
            provider (str, optional): Filter by provider
            
        Returns:
            list: List of IPs matching filters
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
            
        query = {}
        
        if status:
            query["status"] = status
            
        if ip_type:
            query["ip_type"] = ip_type
            
        if country_code:
            query["country_code"] = country_code
            
        if provider:
            query["provider"] = provider
            
        try:
            ips = list(self.collection.find(query).sort("updated_at", -1))
            return ips
        except Exception as e:
            logger.error(f"Error listing IPs: {e}")
            return []
    
    def assign_ip_to_user(self, user_id, ip_id=None, country_code=None, ip_type=None):
        """
        Assign an IP to a user.
        
        Args:
            user_id (str): The user ID
            ip_id (str, optional): Specific IP ID to assign
            country_code (str, optional): Preferred country code
            ip_type (str, optional): Preferred IP type
            
        Returns:
            dict: Assigned IP details or None if assignment failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        # Check if user already has an assigned IP
        user_ips = self.get_user_ips(user_id)
        if user_ips:
            # User already has IPs assigned, return the first one
            logger.info(f"User {user_id} already has {len(user_ips)} IPs assigned")
            return user_ips[0]
            
        # If specific IP requested
        if ip_id:
            ip = self.get_ip(ip_id)
            if not ip:
                logger.warning(f"IP with ID {ip_id} not found")
                return None
                
            if ip["status"] != self.STATUS_AVAILABLE:
                logger.warning(f"IP {ip_id} is not available (status: {ip['status']})")
                return None
                
            if ip["current_users"] >= ip["max_users"]:
                logger.warning(f"IP {ip_id} has reached maximum users")
                return None
                
            # Assign this specific IP
            return self._assign_specific_ip(user_id, ip)
            
        # Find best available IP based on preferences
        query = {
            "status": self.STATUS_AVAILABLE,
            "$expr": {"$lt": ["$current_users", "$max_users"]}
        }
        
        if country_code:
            query["country_code"] = country_code
            
        if ip_type:
            query["ip_type"] = ip_type
            
        # Sort by current_users (ascending), then last_used (ascending) to balance load
        try:
            ip = self.collection.find_one(
                query,
                sort=[("current_users", 1), ("last_used", 1)]
            )
            
            if not ip:
                logger.warning(f"No available IPs matching criteria for user {user_id}")
                
                # Try again without country preference
                if country_code:
                    logger.info(f"Trying to find IP without country preference for user {user_id}")
                    del query["country_code"]
                    ip = self.collection.find_one(
                        query,
                        sort=[("current_users", 1), ("last_used", 1)]
                    )
                
                # Still no IP, try any available IP
                if not ip:
                    logger.warning(f"No available IPs for user {user_id}")
                    return None
            
            return self._assign_specific_ip(user_id, ip)
            
        except Exception as e:
            logger.error(f"Error assigning IP to user: {e}")
            return None
    
    def _assign_specific_ip(self, user_id, ip):
        """
        Helper method to assign a specific IP to a user.
        
        Args:
            user_id (str): The user ID
            ip (dict): The IP document
            
        Returns:
            dict: Updated IP document or None if failed
        """
        try:
            # Update IP document
            result = self.collection.update_one(
                {"_id": ip["_id"]},
                {
                    "$set": {
                        "status": self.STATUS_IN_USE,
                        "last_used": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    "$inc": {"current_users": 1},
                    "$push": {"assigned_users": user_id}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Assigned IP {ip['ip_address']} to user {user_id}")
                
                # Get updated IP document
                updated_ip = self.get_ip(str(ip["_id"]))
                return updated_ip
            else:
                logger.warning(f"Failed to assign IP {ip['ip_address']} to user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error in _assign_specific_ip: {e}")
            return None
    
    def unassign_ip_from_user(self, user_id, ip_id):
        """
        Unassign an IP from a user.
        
        Args:
            user_id (str): The user ID
            ip_id (str): The IP ID
            
        Returns:
            bool: True if unassigned, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            # Get current IP document
            ip = self.get_ip(ip_id)
            if not ip:
                logger.warning(f"IP with ID {ip_id} not found")
                return False
                
            # Check if user is assigned to this IP
            if user_id not in ip["assigned_users"]:
                logger.warning(f"User {user_id} is not assigned to IP {ip_id}")
                return False
                
            # Update IP document
            result = self.collection.update_one(
                {"_id": ObjectId(ip_id)},
                {
                    "$inc": {"current_users": -1},
                    "$pull": {"assigned_users": user_id},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Unassigned IP {ip['ip_address']} from user {user_id}")
                
                # If no more users, update status to cooldown
                updated_ip = self.get_ip(ip_id)
                if updated_ip["current_users"] == 0:
                    self.update_ip_status(ip_id, self.STATUS_COOLDOWN, 
                                         "Automatic cooldown after unassignment")
                    
                    # Schedule to become available after cooldown period
                    # In a real app, this would use a task queue
                    # For now, log the intent
                    logger.info(f"IP {ip['ip_address']} will be available after cooldown period")
                
                return True
            else:
                logger.warning(f"Failed to unassign IP {ip['ip_address']} from user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error unassigning IP from user: {e}")
            return False
    
    def unassign_all_users(self, ip_id):
        """
        Unassign all users from an IP.
        
        Args:
            ip_id (str): The IP ID
            
        Returns:
            bool: True if unassigned, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            # Get current IP document
            ip = self.get_ip(ip_id)
            if not ip:
                logger.warning(f"IP with ID {ip_id} not found")
                return False
                
            # Update IP document
            result = self.collection.update_one(
                {"_id": ObjectId(ip_id)},
                {
                    "$set": {
                        "current_users": 0,
                        "assigned_users": [],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Unassigned all users from IP {ip['ip_address']}")
                return True
            else:
                logger.warning(f"Failed to unassign users from IP {ip['ip_address']}")
                return False
                
        except Exception as e:
            logger.error(f"Error unassigning all users from IP: {e}")
            return False
    
    def get_user_ips(self, user_id):
        """
        Get all IPs assigned to a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            list: List of IP documents
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
            
        try:
            ips = list(self.collection.find({"assigned_users": user_id}))
            return ips
        except Exception as e:
            logger.error(f"Error getting user IPs: {e}")
            return []
    
    def rotate_ip(self, ip_id):
        """
        Rotate an IP (put in cooldown and make previously cooling IPs available).
        
        Args:
            ip_id (str): The IP ID
            
        Returns:
            bool: True if rotated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            # Get current IP document
            ip = self.get_ip(ip_id)
            if not ip:
                logger.warning(f"IP with ID {ip_id} not found")
                return False
                
            # Unassign all users first
            self.unassign_all_users(ip_id)
            
            # Update IP document
            result = self.collection.update_one(
                {"_id": ObjectId(ip_id)},
                {
                    "$set": {
                        "status": self.STATUS_COOLDOWN,
                        "last_rotation": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Rotated IP {ip['ip_address']} to cooldown status")
                
                # Make IPs in cooldown for more than the cooling period available
                cooldown_mins = current_app.config.get('IP_COOLDOWN_MINUTES', 30)
                cooldown_time = datetime.utcnow() - timedelta(minutes=cooldown_mins)
                
                cooldown_result = self.collection.update_many(
                    {
                        "status": self.STATUS_COOLDOWN,
                        "last_rotation": {"$lt": cooldown_time}
                    },
                    {
                        "$set": {
                            "status": self.STATUS_AVAILABLE,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                if cooldown_result.modified_count > 0:
                    logger.info(f"Made {cooldown_result.modified_count} IPs available after cooldown")
                
                return True
            else:
                logger.warning(f"Failed to rotate IP {ip['ip_address']}")
                return False
                
        except Exception as e:
            logger.error(f"Error rotating IP: {e}")
            return False
    
    def report_ip_failure(self, ip_id, failure_type, failure_details=None):
        """
        Report a failure for an IP.
        
        Args:
            ip_id (str): The IP ID
            failure_type (str): Type of failure
            failure_details (str, optional): Additional details
            
        Returns:
            bool: True if reported, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            # Get current IP document
            ip = self.get_ip(ip_id)
            if not ip:
                logger.warning(f"IP with ID {ip_id} not found")
                return False
                
            # Prepare failure record
            failure_record = {
                "type": failure_type,
                "details": failure_details,
                "timestamp": datetime.utcnow()
            }
            
            # Update IP document
            result = self.collection.update_one(
                {"_id": ObjectId(ip_id)},
                {
                    "$inc": {"failure_count": 1},
                    "$push": {"failures": failure_record},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Reported failure for IP {ip['ip_address']}: {failure_type}")
                
                # Check if failure threshold reached
                updated_ip = self.get_ip(ip_id)
                threshold = current_app.config.get('IP_FAILURE_THRESHOLD', 5)
                
                if updated_ip["failure_count"] >= threshold:
                    self.update_ip_status(
                        ip_id, 
                        self.STATUS_FLAGGED, 
                        f"Exceeded failure threshold ({threshold})"
                    )
                
                return True
            else:
                logger.warning(f"Failed to report failure for IP {ip['ip_address']}")
                return False
                
        except Exception as e:
            logger.error(f"Error reporting IP failure: {e}")
            return False
    
    def reset_failure_count(self, ip_id):
        """
        Reset the failure count for an IP.
        
        Args:
            ip_id (str): The IP ID
            
        Returns:
            bool: True if reset, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(ip_id)},
                {
                    "$set": {
                        "failure_count": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            
            if success:
                logger.info(f"Reset failure count for IP {ip_id}")
            else:
                logger.warning(f"Failed to reset failure count for IP {ip_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error resetting failure count: {e}")
            return False
    
    def create_indexes(self):
        """
        Create necessary indexes for the IP collection.
        
        Returns:
            bool: True if indexes created, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            # Index on IP address for quick lookups
            self.collection.create_index("ip_address", unique=True)
            
            # Index on status for filtering available IPs
            self.collection.create_index("status")
            
            # Index on assigned users for finding user's IPs
            self.collection.create_index("assigned_users")
            
            # Compound index for finding suitable IPs
            self.collection.create_index([
                ("status", 1),
                ("current_users", 1),
                ("country_code", 1),
                ("ip_type", 1)
            ])
            
            logger.info("Created indexes for IP collection")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False
