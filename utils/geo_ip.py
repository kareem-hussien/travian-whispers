"""
Geolocation utilities for Travian Whispers application.
This module provides IP geolocation functions for the IP management system.
"""
import logging
import os
import socket
import requests
from datetime import datetime, timedelta
from flask import current_app

# Import config
from config.ip_config import GEO_DATABASE_PATH, GEO_DEFAULT_COUNTRY

# Initialize logger
logger = logging.getLogger(__name__)

# Try to import MaxMind GeoIP (if installed)
try:
    import geoip2.database
    MAXMIND_AVAILABLE = True
except ImportError:
    MAXMIND_AVAILABLE = False
    logger.warning("MaxMind GeoIP2 package not available. Using fallback geolocation methods.")

class GeoIPManager:
    """Manager for IP geolocation operations."""
    
    def __init__(self):
        """Initialize the GeoIPManager."""
        self.geoip_reader = None
        self.ip_cache = {}
        self.cache_expiry = timedelta(days=7)  # Cache entries for 7 days
        
        # Initialize MaxMind database if available
        if MAXMIND_AVAILABLE and os.path.exists(GEO_DATABASE_PATH):
            try:
                self.geoip_reader = geoip2.database.Reader(GEO_DATABASE_PATH)
                logger.info(f"Initialized MaxMind GeoIP database from {GEO_DATABASE_PATH}")
            except Exception as e:
                logger.error(f"Failed to initialize MaxMind GeoIP database: {e}")
    
    def get_ip_info(self, ip_address):
        """
        Get geolocation information for an IP address.
        
        Args:
            ip_address (str): IP address to lookup
            
        Returns:
            dict: Geolocation information or None if not found
        """
        # Check cache first
        now = datetime.utcnow()
        if ip_address in self.ip_cache:
            entry = self.ip_cache[ip_address]
            if now - entry['timestamp'] < self.cache_expiry:
                return entry['data']
            else:
                # Entry expired, remove from cache
                del self.ip_cache[ip_address]
        
        # Try MaxMind first if available
        if self.geoip_reader:
            try:
                response = self.geoip_reader.city(ip_address)
                
                geo_info = {
                    'ip': ip_address,
                    'country_code': response.country.iso_code,
                    'country_name': response.country.name,
                    'region': response.subdivisions.most_specific.iso_code if response.subdivisions else None,
                    'region_name': response.subdivisions.most_specific.name if response.subdivisions else None,
                    'city': response.city.name,
                    'postal_code': response.postal.code,
                    'latitude': response.location.latitude,
                    'longitude': response.location.longitude,
                    'source': 'maxmind'
                }
                
                # Cache the result
                self.ip_cache[ip_address] = {
                    'timestamp': now,
                    'data': geo_info
                }
                
                return geo_info
            except Exception as e:
                logger.error(f"MaxMind lookup failed for IP {ip_address}: {e}")
        
        # Fall back to ip-api.com
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}")
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    geo_info = {
                        'ip': ip_address,
                        'country_code': data.get('countryCode'),
                        'country_name': data.get('country'),
                        'region': data.get('region'),
                        'region_name': data.get('regionName'),
                        'city': data.get('city'),
                        'postal_code': data.get('zip'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'source': 'ip-api'
                    }
                    
                    # Cache the result
                    self.ip_cache[ip_address] = {
                        'timestamp': now,
                        'data': geo_info
                    }
                    
                    return geo_info
        except Exception as e:
            logger.error(f"ip-api.com lookup failed for IP {ip_address}: {e}")
        
        # Last fallback: return minimal info with default country
        logger.warning(f"Could not determine geolocation for IP {ip_address}, using defaults")
        geo_info = {
            'ip': ip_address,
            'country_code': GEO_DEFAULT_COUNTRY,
            'country_name': 'Unknown',
            'region': None,
            'region_name': None,
            'city': None,
            'postal_code': None,
            'latitude': None,
            'longitude': None,
            'source': 'default'
        }
        
        # Cache the result
        self.ip_cache[ip_address] = {
            'timestamp': now,
            'data': geo_info
        }
        
        return geo_info
    
    def get_user_location(self, user_id):
        """
        Get a user's location based on their login patterns.
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Location information or default
        """
        try:
            # This would typically get the last known location from user history
            # For now, we'll return a placeholder implementation
            
            # In a real implementation, this would query the user's login history
            # from the database and determine their typical location
            from database.models.user import User
            user_model = User()
            user = user_model.get_user_by_id(user_id)
            
            if not user:
                logger.warning(f"User {user_id} not found")
                return {'country_code': GEO_DEFAULT_COUNTRY}
            
            # For now, return default country
            return {'country_code': GEO_DEFAULT_COUNTRY}
            
        except Exception as e:
            logger.error(f"Error getting user location: {e}")
            return {'country_code': GEO_DEFAULT_COUNTRY}
    
    def match_ip_to_user_location(self, user_id, available_ips):
        """
        Match a user to an IP in their typical location.
        
        Args:
            user_id (str): User ID
            available_ips (list): List of available IP documents
            
        Returns:
            dict: Best matching IP or None if no match
        """
        if not available_ips:
            return None
        
        try:
            # Get user's typical location
            user_location = self.get_user_location(user_id)
            target_country = user_location.get('country_code', GEO_DEFAULT_COUNTRY)
            
            # Find IPs that match the user's country
            matching_ips = []
            for ip in available_ips:
                ip_country = ip.get('country_code')
                
                if ip_country and ip_country == target_country:
                    matching_ips.append(ip)
            
            # If we found matching IPs, return one of them
            if matching_ips:
                # Choose the one with the least current users
                matching_ips.sort(key=lambda x: x.get('current_users', 0))
                logger.info(f"Found matching IP in {target_country} for user {user_id}")
                return matching_ips[0]
            
            # No match found, return any available IP
            logger.warning(f"No IPs found in {target_country} for user {user_id}, using any available IP")
            
            # Sort by current users (ascending)
            available_ips.sort(key=lambda x: x.get('current_users', 0))
            return available_ips[0]
            
        except Exception as e:
            logger.error(f"Error matching IP to user location: {e}")
            
            # On error, return the first available IP
            if available_ips:
                return available_ips[0]
            return None
    
    def get_my_ip(self):
        """
        Get this server's public IP address.
        
        Returns:
            str: Public IP address or None if not found
        """
        try:
            # Try multiple services
            services = [
                "https://api.ipify.org",
                "https://api.my-ip.io/ip",
                "https://ipinfo.io/ip"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        # Validate IP format
                        socket.inet_aton(ip)
                        return ip
                except:
                    continue
            
            logger.warning("Could not determine server's public IP using external services")
            
            # Fallback: try socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except:
                logger.error("Failed to determine server's IP address")
                return None
                
        except Exception as e:
            logger.error(f"Error getting server IP: {e}")
            return None

# Create a singleton instance
geo_ip_manager = GeoIPManager()
