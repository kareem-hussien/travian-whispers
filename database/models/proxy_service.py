"""
Proxy Service model for Travian Whispers application.
This module provides the ProxyService model for managing proxy providers and integration.
"""
import logging
import requests
import json
from datetime import datetime
from bson import ObjectId
from flask import current_app
from database.models.ip_pool import IPAddress

# Initialize logger
logger = logging.getLogger(__name__)


class ProxyService:
    """ProxyService model for managing proxy providers and IP acquisition."""
    
    # Proxy Provider Types
    PROVIDER_LUMINATI = 'luminati'
    PROVIDER_OXYLABS = 'oxylabs'
    PROVIDER_SMARTPROXY = 'smartproxy'
    PROVIDER_BRIGHTDATA = 'brightdata'
    PROVIDER_CUSTOM = 'custom'
    
    def __init__(self):
        """Initialize ProxyService model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["proxyServices"]
    
    def add_provider(self, name, provider_type, api_key=None, username=None, 
                    password=None, endpoint=None, config=None):
        """
        Add a new proxy provider.
        
        Args:
            name (str): Provider name
            provider_type (str): Provider type (from PROVIDER_ constants)
            api_key (str, optional): API key for the provider
            username (str, optional): Username for the provider
            password (str, optional): Password for the provider
            endpoint (str, optional): API endpoint
            config (dict, optional): Additional provider configuration
            
        Returns:
            dict: The created provider document or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        # Check if provider already exists
        existing_provider = self.collection.find_one({"name": name})
        if existing_provider:
            logger.warning(f"Provider {name} already exists")
            return existing_provider
            
        provider_data = {
            "name": name,
            "type": provider_type,
            "api_key": api_key,
            "username": username,
            "password": password,
            "endpoint": endpoint,
            "config": config or {},
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_fetch": None,
            "fetch_count": 0,
            "success_rate": 100.0,
            "error_count": 0
        }
        
        try:
            result = self.collection.insert_one(provider_data)
            if result.inserted_id:
                provider_data["_id"] = result.inserted_id
                logger.info(f"Added new proxy provider: {name}")
                return provider_data
            return None
        except Exception as e:
            logger.error(f"Failed to add proxy provider: {e}")
            return None
    
    def get_provider(self, provider_id):
        """
        Get a provider by ID.
        
        Args:
            provider_id (str): The provider ID
            
        Returns:
            dict: Provider details or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        try:
            provider = self.collection.find_one({"_id": ObjectId(provider_id)})
            return provider
        except Exception as e:
            logger.error(f"Error getting provider: {e}")
            return None
    
    def get_provider_by_name(self, name):
        """
        Get a provider by name.
        
        Args:
            name (str): The provider name
            
        Returns:
            dict: Provider details or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        try:
            provider = self.collection.find_one({"name": name})
            return provider
        except Exception as e:
            logger.error(f"Error getting provider by name: {e}")
            return None
    
    def list_providers(self, active_only=True):
        """
        List all proxy providers.
        
        Args:
            active_only (bool, optional): Only return active providers
            
        Returns:
            list: List of providers
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
            
        query = {}
        if active_only:
            query["is_active"] = True
            
        try:
            providers = list(self.collection.find(query))
            return providers
        except Exception as e:
            logger.error(f"Error listing providers: {e}")
            return []
    
    def update_provider(self, provider_id, update_data):
        """
        Update a proxy provider.
        
        Args:
            provider_id (str): The provider ID
            update_data (dict): Data to update
            
        Returns:
            bool: True if updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        # Don't allow updating these fields directly
        protected_fields = ["_id", "created_at", "fetch_count", "error_count"]
        for field in protected_fields:
            if field in update_data:
                del update_data[field]
                
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(provider_id)},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            
            if success:
                logger.info(f"Updated provider {provider_id}")
            else:
                logger.warning(f"Failed to update provider {provider_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error updating provider: {e}")
            return False
    
    def delete_provider(self, provider_id):
        """
        Delete a proxy provider.
        
        Args:
            provider_id (str): The provider ID
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            result = self.collection.delete_one({"_id": ObjectId(provider_id)})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted provider {provider_id}")
            else:
                logger.warning(f"Failed to delete provider {provider_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error deleting provider: {e}")
            return False
    
    def fetch_proxies(self, provider_id, country_code=None, ip_type=None, 
                     count=10, update_pool=True):
        """
        Fetch proxies from a provider.
        
        Args:
            provider_id (str): The provider ID
            country_code (str, optional): Filter by country code
            ip_type (str, optional): Filter by IP type
            count (int, optional): Number of proxies to fetch
            update_pool (bool, optional): Whether to update the IP pool
            
        Returns:
            list: List of proxy dictionaries or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
            
        # Get provider details
        provider = self.get_provider(provider_id)
        if not provider:
            logger.error(f"Provider with ID {provider_id} not found")
            return None
            
        proxies = []
        
        try:
            # Increment fetch count
            self.collection.update_one(
                {"_id": ObjectId(provider_id)},
                {
                    "$inc": {"fetch_count": 1},
                    "$set": {"last_fetch": datetime.utcnow()}
                }
            )
            
            # Fetch based on provider type
            if provider["type"] == self.PROVIDER_LUMINATI:
                proxies = self._fetch_luminati_proxies(provider, country_code, ip_type, count)
            elif provider["type"] == self.PROVIDER_OXYLABS:
                proxies = self._fetch_oxylabs_proxies(provider, country_code, ip_type, count)
            elif provider["type"] == self.PROVIDER_SMARTPROXY:
                proxies = self._fetch_smartproxy_proxies(provider, country_code, ip_type, count)
            elif provider["type"] == self.PROVIDER_BRIGHTDATA:
                proxies = self._fetch_brightdata_proxies(provider, country_code, ip_type, count)
            elif provider["type"] == self.PROVIDER_CUSTOM:
                proxies = self._fetch_custom_proxies(provider, country_code, ip_type, count)
            else:
                logger.error(f"Unknown provider type: {provider['type']}")
                return None
                
            # Update success rate
            if proxies:
                self.collection.update_one(
                    {"_id": ObjectId(provider_id)},
                    {"$set": {"success_rate": 100.0}}
                )
            else:
                self.collection.update_one(
                    {"_id": ObjectId(provider_id)},
                    {
                        "$inc": {"error_count": 1},
                        "$set": {"success_rate": 0.0}
                    }
                )
                
            # Update IP pool if requested
            if update_pool and proxies:
                self._add_proxies_to_pool(proxies, provider)
                
            return proxies
        except Exception as e:
            # Log error and update error count
            logger.error(f"Error fetching proxies: {e}")
            self.collection.update_one(
                {"_id": ObjectId(provider_id)},
                {
                    "$inc": {"error_count": 1},
                    "$set": {"success_rate": 0.0}
                }
            )
            return None
    
    def _fetch_luminati_proxies(self, provider, country_code, ip_type, count):
        """
        Fetch proxies from Luminati (Bright Data).
        
        Args:
            provider (dict): Provider details
            country_code (str): Country code filter
            ip_type (str): IP type filter
            count (int): Number of proxies to fetch
            
        Returns:
            list: List of proxy dictionaries
        """
        proxies = []
        endpoint = provider["endpoint"] or "https://api.brightdata.com/zone/ips"
        
        # Prepare request parameters
        params = {
            "auth": provider["api_key"],
            "zone": provider["config"].get("zone", ""),
            "limit": count
        }
        
        if country_code:
            params["country"] = country_code
            
        # Map IP types to Luminati's types
        if ip_type:
            if ip_type == IPAddress.TYPE_RESIDENTIAL:
                params["ip_type"] = "residential"
            elif ip_type == IPAddress.TYPE_MOBILE:
                params["ip_type"] = "mobile"
            elif ip_type == IPAddress.TYPE_DATACENTER:
                params["ip_type"] = "datacenter"
                
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for ip_data in data:
                proxy = {
                    "ip_address": ip_data["ip"],
                    "proxy_url": f"{provider['username']}-{country_code if country_code else 'any'}.{provider['config'].get('zone', '')}.brightdata.com:{provider['config'].get('port', '22225')}",
                    "username": provider["username"],
                    "password": provider["password"],
                    "country_code": ip_data.get("country", ""),
                    "region": ip_data.get("region", ""),
                    "ip_type": IPAddress.TYPE_RESIDENTIAL if ip_data.get("type") == "residential" else (
                        IPAddress.TYPE_MOBILE if ip_data.get("type") == "mobile" else IPAddress.TYPE_DATACENTER
                    ),
                    "provider": provider["name"],
                    "max_users": provider["config"].get("max_users_per_ip", 1)
                }
                proxies.append(proxy)
                
            return proxies
        except Exception as e:
            logger.error(f"Error fetching Luminati proxies: {e}")
            return []
    
    def _fetch_oxylabs_proxies(self, provider, country_code, ip_type, count):
        """
        Fetch proxies from Oxylabs.
        
        Args:
            provider (dict): Provider details
            country_code (str): Country code filter
            ip_type (str): IP type filter
            count (int): Number of proxies to fetch
            
        Returns:
            list: List of proxy dictionaries
        """
        proxies = []
        endpoint = provider["endpoint"] or "https://api.oxylabs.io/v1/proxies"
        
        # Prepare headers with authentication
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        # Prepare request body
        body = {
            "limit": count
        }
        
        if country_code:
            body["country"] = country_code
            
        # Map IP types to Oxylabs' types
        if ip_type:
            if ip_type == IPAddress.TYPE_RESIDENTIAL:
                body["type"] = "residential"
            elif ip_type == IPAddress.TYPE_MOBILE:
                body["type"] = "mobile"
            elif ip_type == IPAddress.TYPE_DATACENTER:
                body["type"] = "datacenter"
                
        try:
            response = requests.post(endpoint, headers=headers, json=body)
            response.raise_for_status()
            
            data = response.json()
            
            for ip_data in data.get("proxies", []):
                proxy = {
                    "ip_address": ip_data["ip"],
                    "proxy_url": f"{ip_data['ip']}:{provider['config'].get('port', '7777')}",
                    "username": provider["username"],
                    "password": provider["password"],
                    "country_code": ip_data.get("country", ""),
                    "region": ip_data.get("region", ""),
                    "ip_type": IPAddress.TYPE_RESIDENTIAL if ip_data.get("type") == "residential" else (
                        IPAddress.TYPE_MOBILE if ip_data.get("type") == "mobile" else IPAddress.TYPE_DATACENTER
                    ),
                    "provider": provider["name"],
                    "max_users": provider["config"].get("max_users_per_ip", 1)
                }
                proxies.append(proxy)
                
            return proxies
        except Exception as e:
            logger.error(f"Error fetching Oxylabs proxies: {e}")
            return []
    
    def _fetch_smartproxy_proxies(self, provider, country_code, ip_type, count):
        """
        Fetch proxies from Smartproxy.
        
        Args:
            provider (dict): Provider details
            country_code (str): Country code filter
            ip_type (str): IP type filter
            count (int): Number of proxies to fetch
            
        Returns:
            list: List of proxy dictionaries
        """
        proxies = []
        endpoint = provider["endpoint"] or "https://api.smartproxy.com/v1/endpoints"
        
        # Prepare headers with authentication
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Filter and transform the data
            filtered_proxies = []
            
            for endpoint in data.get("endpoints", []):
                # Apply filters
                if country_code and endpoint.get("country_code") != country_code:
                    continue
                    
                proxy_type = None
                if endpoint.get("proxy_type") == "residential":
                    proxy_type = IPAddress.TYPE_RESIDENTIAL
                elif endpoint.get("proxy_type") == "mobile":
                    proxy_type = IPAddress.TYPE_MOBILE
                elif endpoint.get("proxy_type") == "datacenter":
                    proxy_type = IPAddress.TYPE_DATACENTER
                else:
                    proxy_type = IPAddress.TYPE_DATACENTER
                    
                if ip_type and proxy_type != ip_type:
                    continue
                    
                filtered_proxies.append({
                    "endpoint": endpoint
                })
                
                if len(filtered_proxies) >= count:
                    break
            
            # Create proxy objects
            for item in filtered_proxies:
                endpoint = item["endpoint"]
                proxy = {
                    "ip_address": endpoint.get("ip", ""),
                    "proxy_url": f"{endpoint.get('host', '')}:{endpoint.get('port', '10000')}",
                    "username": provider["username"],
                    "password": provider["password"],
                    "country_code": endpoint.get("country_code", ""),
                    "region": endpoint.get("region", ""),
                    "ip_type": proxy_type,
                    "provider": provider["name"],
                    "max_users": provider["config"].get("max_users_per_ip", 1)
                }
                proxies.append(proxy)
                
            return proxies
        except Exception as e:
            logger.error(f"Error fetching Smartproxy proxies: {e}")
            return []
    
    def _fetch_brightdata_proxies(self, provider, country_code, ip_type, count):
        """
        Fetch proxies from Brightdata (same API as Luminati).
        
        Args:
            provider (dict): Provider details
            country_code (str): Country code filter
            ip_type (str): IP type filter
            count (int): Number of proxies to fetch
            
        Returns:
            list: List of proxy dictionaries
        """
        # Brightdata uses the same API as Luminati
        return self._fetch_luminati_proxies(provider, country_code, ip_type, count)
    
    def _fetch_custom_proxies(self, provider, country_code, ip_type, count):
        """
        Fetch proxies from a custom provider.
        
        Args:
            provider (dict): Provider details
            country_code (str): Country code filter
            ip_type (str): IP type filter
            count (int): Number of proxies to fetch
            
        Returns:
            list: List of proxy dictionaries
        """
        proxies = []
        endpoint = provider["endpoint"]
        
        if not endpoint:
            logger.error("Custom provider requires an endpoint")
            return []
        
        # Prepare headers and parameters based on provider config
        headers = {}
        params = {}
        
        if provider["api_key"]:
            headers["Authorization"] = f"Bearer {provider['api_key']}"
            
        if provider["config"].get("auth_header"):
            headers[provider["config"]["auth_header"]] = provider["config"]["auth_value"]
            
        if country_code:
            params[provider["config"].get("country_param", "country")] = country_code
            
        if ip_type:
            params[provider["config"].get("type_param", "type")] = ip_type
            
        params[provider["config"].get("limit_param", "limit")] = count
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract proxies based on provider's JSON mapping
            item_path = provider["config"].get("item_path", "")
            items = data
            
            if item_path:
                for key in item_path.split('.'):
                    items = items.get(key, [])
            
            ip_field = provider["config"].get("ip_field", "ip")
            port_field = provider["config"].get("port_field", "port")
            country_field = provider["config"].get("country_field", "country")
            region_field = provider["config"].get("region_field", "region")
            type_field = provider["config"].get("type_field", "type")
            
            for item in items:
                ip = item.get(ip_field, "")
                port = item.get(port_field, "")
                
                proxy_type = IPAddress.TYPE_DATACENTER
                raw_type = item.get(type_field, "").lower()
                
                if "residential" in raw_type:
                    proxy_type = IPAddress.TYPE_RESIDENTIAL
                elif "mobile" in raw_type:
                    proxy_type = IPAddress.TYPE_MOBILE
                
                proxy = {
                    "ip_address": ip,
                    "proxy_url": f"{ip}:{port}",
                    "username": provider["username"],
                    "password": provider["password"],
                    "country_code": item.get(country_field, ""),
                    "region": item.get(region_field, ""),
                    "ip_type": proxy_type,
                    "provider": provider["name"],
                    "max_users": provider["config"].get("max_users_per_ip", 1)
                }
                proxies.append(proxy)
                
            return proxies
        except Exception as e:
            logger.error(f"Error fetching custom proxies: {e}")
            return []
    
    def _add_proxies_to_pool(self, proxies, provider):
        """
        Add fetched proxies to the IP pool.
        
        Args:
            proxies (list): List of proxy dictionaries
            provider (dict): Provider details
            
        Returns:
            int: Number of proxies added
        """
        ip_pool = IPAddress()
        added_count = 0
        
        for proxy in proxies:
            # Check if IP already exists
            existing_ip = ip_pool.get_ip_by_address(proxy["ip_address"])
            
            if existing_ip:
                logger.debug(f"IP {proxy['ip_address']} already exists in pool")
                continue
                
            # Add to pool
            ip = ip_pool.add_ip(
                ip_address=proxy["ip_address"],
                proxy_url=proxy["proxy_url"],
                username=proxy["username"],
                password=proxy["password"],
                ip_type=proxy["ip_type"],
                country_code=proxy["country_code"],
                region=proxy["region"],
                provider=proxy["provider"],
                max_users=proxy["max_users"]
            )
            
            if ip:
                added_count += 1
                
        logger.info(f"Added {added_count} new proxies to the IP pool from {provider['name']}")
        return added_count
    
    def auto_fetch_proxies(self, min_available=20):
        """
        Automatically fetch proxies if available count is below threshold.
        
        Args:
            min_available (int, optional): Minimum available IPs threshold
            
        Returns:
            int: Number of new proxies fetched
        """
        # Check current available IP count
        ip_pool = IPAddress()
        available_ips = ip_pool.list_ips(status=IPAddress.STATUS_AVAILABLE)
        
        if len(available_ips) >= min_available:
            logger.info(f"Sufficient IPs available ({len(available_ips)}), skipping auto-fetch")
            return 0
            
        # Calculate how many to fetch
        to_fetch = min_available - len(available_ips)
        
        # Get active providers
        providers = self.list_providers(active_only=True)
        
        if not providers:
            logger.warning("No active proxy providers available for auto-fetch")
            return 0
            
        total_fetched = 0
        
        # Fetch from each provider
        for provider in providers:
            # Skip if we've already fetched enough
            if total_fetched >= to_fetch:
                break
                
            # Fetch proxies
            provider_id = str(provider["_id"])
            proxies = self.fetch_proxies(
                provider_id=provider_id,
                count=to_fetch - total_fetched,
                update_pool=True
            )
            
            if proxies:
                total_fetched += len(proxies)
                
        logger.info(f"Auto-fetched {total_fetched} new proxies")
        return total_fetched
    
    def create_indexes(self):
        """
        Create necessary indexes for the proxy services collection.
        
        Returns:
            bool: True if indexes created, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
            
        try:
            # Index on name for unique providers
            self.collection.create_index("name", unique=True)
            
            # Index on type for filtering
            self.collection.create_index("type")
            
            # Index on active status
            self.collection.create_index("is_active")
            
            logger.info("Created indexes for proxy services collection")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False