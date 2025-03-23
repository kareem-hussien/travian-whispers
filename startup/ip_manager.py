"""
IP Manager module for Travian Whispers application.
This module provides utilities for managing and rotating proxied IPs.
"""
import logging
import random
import time
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId

# Initialize logger
logger = logging.getLogger(__name__)

class IPManager:
    """Manager for IP allocation and rotation."""
    
    def __init__(self, db_uri=None):
        """
        Initialize IPManager.
        
        Args:
            db_uri (str, optional): MongoDB connection URI
        """
        # Initialize MongoDB connection
        if db_uri:
            self.client = MongoClient(db_uri)
        else:
            # Use default connection from environment or config
            from startup.db_config import get_db_client
            self.client = get_db_client()
            
        # Get database and collections
        self.db = self.client['travian_whispers']
        self.ip_collection = self.db['proxied_ips']
        self.ip_assignments = self.db['ip_assignments']
        
        # Create indexes if they don't exist
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure required indexes exist in MongoDB collections."""
        # IP collection indexes
        self.ip_collection.create_index("ip", unique=True)
        self.ip_collection.create_index("status")
        self.ip_collection.create_index("lastRotated")
        
        # IP assignments indexes
        self.ip_assignments.create_index("userId", unique=True)
        self.ip_assignments.create_index("ipId")
        self.ip_assignments.create_index("assignedAt")
    
    def list_available_ips(self):
        """
        List all available IPs.
        
        Returns:
            list: List of available IP documents
        """
        return list(self.ip_collection.find({"status": "available"}))
    
    def get_ip_for_user(self, user_id):
        """
        Get or assign an IP for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            dict: IP data or None if no IPs available
        """
        # Check if user already has an assigned IP
        existing_assignment = self.ip_assignments.find_one({"userId": user_id})
        
        if existing_assignment:
            # Get the IP data
            ip_data = self.ip_collection.find_one({"_id": ObjectId(existing_assignment["ipId"])})
            
            if ip_data and ip_data["status"] not in ["banned", "error"]:
                # Update last used timestamp
                self.ip_collection.update_one(
                    {"_id": ObjectId(existing_assignment["ipId"])},
                    {"$set": {"lastUsed": datetime.utcnow()}}
                )
                
                # User already has a valid IP assignment
                return ip_data
            else:
                # IP is no longer valid, remove assignment
                self.ip_assignments.delete_one({"_id": existing_assignment["_id"]})
        
        # Find an available IP
        available_ips = list(self.ip_collection.find(
            {"status": "available", "inUse": False},
            sort=[("lastUsed", 1)]  # Get least recently used IP first
        ))
        
        if not available_ips:
            logger.error(f"No available IPs for user {user_id}")
            return None
        
        # Get the first available IP
        selected_ip = available_ips[0]
        
        # Mark IP as in use
        self.ip_collection.update_one(
            {"_id": selected_ip["_id"]},
            {"$set": {
                "inUse": True,
                "lastUsed": datetime.utcnow()
            }}
        )
        
        # Create assignment
        assignment = {
            "userId": user_id,
            "ipId": str(selected_ip["_id"]),
            "assignedAt": datetime.utcnow()
        }
        
        self.ip_assignments.insert_one(assignment)
        
        logger.info(f"Assigned IP {selected_ip['ip']} to user {user_id}")
        
        return selected_ip
    
    def release_ip_for_user(self, user_id):
        """
        Release an IP assignment for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            bool: True if IP was released, False otherwise
        """
        # Get the current assignment
        assignment = self.ip_assignments.find_one({"userId": user_id})
        
        if not assignment:
            # No assignment to release
            return False
        
        # Release the IP
        self.ip_collection.update_one(
            {"_id": ObjectId(assignment["ipId"])},
            {"$set": {"inUse": False}}
        )
        
        # Remove the assignment
        self.ip_assignments.delete_one({"_id": assignment["_id"]})
        
        logger.info(f"Released IP assignment for user {user_id}")
        
        return True
    
    def rotate_ip_for_user(self, user_id):
        """
        Rotate the IP for a user.
        
        Args:
            user_id (str): The user ID
            
        Returns:
            dict: New IP data or None if no IPs available
        """
        # Release current IP
        self.release_ip_for_user(user_id)
        
        # Get a new IP
        new_ip = self.get_ip_for_user(user_id)
        
        if new_ip:
            logger.info(f"Rotated IP for user {user_id} to {new_ip['ip']}")
        
        return new_ip
    
    def add_ip(self, ip, port, username=None, password=None, proxy_type="http"):
        """
        Add a new IP to the pool.
        
        Args:
            ip (str): The IP address
            port (int): The port number
            username (str, optional): Proxy username
            password (str, optional): Proxy password
            proxy_type (str, optional): Proxy type (http, socks5)
            
        Returns:
            str: ID of the new IP document or None if error
        """
        # Check if IP already exists
        existing = self.ip_collection.find_one({"ip": ip})
        
        if existing:
            logger.warning(f"IP {ip} already exists in the pool")
            return str(existing["_id"])
        
        # Create new IP document
        ip_doc = {
            "ip": ip,
            "port": port,
            "username": username,
            "password": password,
            "proxyType": proxy_type,
            "status": "available",
            "inUse": False,
            "lastUsed": None,
            "lastRotated": datetime.utcnow(),
            "errorCount": 0,
            "banCount": 0
        }
        
        # Insert into collection
        result = self.ip_collection.insert_one(ip_doc)
        
        if result.inserted_id:
            logger.info(f"Added new IP {ip} to the pool")
            return str(result.inserted_id)
        else:
            logger.error(f"Failed to add IP {ip} to the pool")
            return None
    
    def remove_ip(self, ip_id):
        """
        Remove an IP from the pool.
        
        Args:
            ip_id (str): The IP document ID
            
        Returns:
            bool: True if IP was removed, False otherwise
        """
        # Convert string ID to ObjectId
        obj_id = ObjectId(ip_id)
        
        # Check if IP is in use
        ip_doc = self.ip_collection.find_one({"_id": obj_id})
        
        if not ip_doc:
            logger.warning(f"IP with ID {ip_id} not found")
            return False
        
        if ip_doc["inUse"]:
            # IP is in use, find and release assignment
            assignment = self.ip_assignments.find_one({"ipId": ip_id})
            
            if assignment:
                # Remove assignment
                self.ip_assignments.delete_one({"_id": assignment["_id"]})
                logger.info(f"Released assignment for IP {ip_doc['ip']}")
        
        # Remove IP
        result = self.ip_collection.delete_one({"_id": obj_id})
        
        if result.deleted_count > 0:
            logger.info(f"Removed IP {ip_doc['ip']} from the pool")
            return True
        else:
            logger.error(f"Failed to remove IP {ip_doc['ip']} from the pool")
            return False
    
    def report_ip_failure(self, ip_id, error_type, error_message):
        """
        Report an IP failure.
        
        Args:
            ip_id (str): The IP document ID
            error_type (str): Type of error
            error_message (str): Error message
            
        Returns:
            bool: True if report was recorded, False otherwise
        """
        # Convert string ID to ObjectId if needed
        obj_id = ObjectId(ip_id) if not isinstance(ip_id, ObjectId) else ip_id
        
        # Update IP document
        result = self.ip_collection.update_one(
            {"_id": obj_id},
            {
                "$inc": {"errorCount": 1},
                "$set": {
                    "lastError": {
                        "type": error_type,
                        "message": error_message,
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )
        
        if result.modified_count > 0:
            logger.warning(f"IP failure reported: {error_type} - {error_message}")
            return True
        else:
            logger.error(f"Failed to report IP failure for ID {ip_id}")
            return False
    
    def report_ip_ban(self, ip_id, ban_reason):
        """
        Report an IP as banned.
        
        Args:
            ip_id (str): The IP document ID
            ban_reason (str): Reason for the ban
            
        Returns:
            bool: True if IP was marked as banned, False otherwise
        """
        # Convert string ID to ObjectId if needed
        obj_id = ObjectId(ip_id) if not isinstance(ip_id, ObjectId) else ip_id
        
        # Update IP document
        result = self.ip_collection.update_one(
            {"_id": obj_id},
            {
                "$inc": {"banCount": 1},
                "$set": {
                    "status": "banned",
                    "banReason": ban_reason,
                    "bannedAt": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.warning(f"IP marked as banned: {ban_reason}")
            
            # Release any assignments for this IP
            assignments = self.ip_assignments.find({"ipId": str(obj_id)})
            
            for assignment in assignments:
                self.ip_assignments.delete_one({"_id": assignment["_id"]})
                logger.info(f"Released assignment for banned IP, user {assignment['userId']}")
            
            return True
        else:
            logger.error(f"Failed to mark IP as banned for ID {ip_id}")
            return False
    
    def get_proxy_url(self, ip_data):
        """
        Get a proxy URL string from IP data.
        
        Args:
            ip_data (dict): IP document data
            
        Returns:
            str: Proxy URL string or None if invalid data
        """
        if not ip_data or "ip" not in ip_data or "port" not in ip_data:
            return None
        
        proxy_type = ip_data.get("proxyType", "http")
        
        # Build basic proxy URL
        proxy_url = f"{proxy_type}://{ip_data['ip']}:{ip_data['port']}"
        
        # Add authentication if available
        if ip_data.get("username") and ip_data.get("password"):
            proxy_url = f"{proxy_type}://{ip_data['username']}:{ip_data['password']}@{ip_data['ip']}:{ip_data['port']}"
        
        return proxy_url
    
    def schedule_ip_rotation(self, max_age_hours=24):
        """
        Schedule IP rotation for IPs that have been used for too long.
        
        Args:
            max_age_hours (int, optional): Maximum age in hours
            
        Returns:
            int: Number of IPs rotated
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Find IPs that need rotation
        ips_to_rotate = self.ip_collection.find({
            "status": "available",
            "lastRotated": {"$lt": cutoff_time}
        })
        
        rotated_count = 0
        
        for ip in ips_to_rotate:
            # Mark IP for rotation
            self.ip_collection.update_one(
                {"_id": ip["_id"]},
                {"$set": {
                    "status": "rotating",
                    "lastRotated": datetime.utcnow()
                }}
            )
            
            # Find assignments for this IP
            assignments = list(self.ip_assignments.find({"ipId": str(ip["_id"])}))
            
            for assignment in assignments:
                # Get new IP for user
                new_ip = self.get_ip_for_user(assignment["userId"])
                
                if new_ip:
                    # Remove old assignment
                    self.ip_assignments.delete_one({"_id": assignment["_id"]})
                    logger.info(f"Rotated IP for user {assignment['userId']} as part of scheduled rotation")
            
            # Mark IP as available again
            self.ip_collection.update_one(
                {"_id": ip["_id"]},
                {"$set": {
                    "status": "available",
                    "inUse": False
                }}
            )
            
            rotated_count += 1
        
        logger.info(f"Rotated {rotated_count} IPs as part of scheduled rotation")
        
        return rotated_count
