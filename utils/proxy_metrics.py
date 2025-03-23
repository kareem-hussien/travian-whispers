"""
Proxy Metrics module for Travian Whispers application.
This module provides metrics collection and monitoring for proxy performance.
"""
import logging
import time
from datetime import datetime, timedelta
from flask import current_app
from database.models.ip_pool import IPAddress
from database.models.proxy_service import ProxyService

# Initialize logger
logger = logging.getLogger(__name__)


class ProxyMetrics:
    """Collects and analyzes proxy performance metrics."""
    
    def __init__(self):
        """Initialize ProxyMetrics."""
        self.ip_pool = IPAddress()
        self.proxy_service = ProxyService()
        self.metrics_collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            self.metrics_collection = self.db["proxyMetrics"]
    
    def record_proxy_usage(self, ip_id, request_url, success, response_time=None, status_code=None, error=None):
        """
        Record proxy usage metrics.
        
        Args:
            ip_id (str): The IP ID
            request_url (str): The URL that was requested
            success (bool): Whether the request was successful
            response_time (float, optional): Response time in seconds
            status_code (int, optional): HTTP status code
            error (str, optional): Error message if failed
            
        Returns:
            bool: True if recorded, False otherwise
        """
        if self.metrics_collection is None:
            logger.error("Database not connected")
            return False
        
        # Get IP details
        ip = self.ip_pool.get_ip(ip_id)
        if not ip:
            logger.warning(f"IP with ID {ip_id} not found")
            return False
        
        # Prepare metrics data
        metrics_data = {
            "ip_id": ip_id,
            "ip_address": ip.get("ip_address"),
            "provider": ip.get("provider"),
            "request_url": request_url,
            "success": success,
            "response_time": response_time,
            "status_code": status_code,
            "error": error,
            "timestamp": datetime.utcnow()
        }
        
        try:
            # Insert metrics record
            result = self.metrics_collection.insert_one(metrics_data)
            
            if result.inserted_id:
                # Update IP success/failure stats
                if not success:
                    self.ip_pool.report_ip_failure(
                        ip_id,
                        "request_failure",
                        f"URL: {request_url}, Error: {error}"
                    )
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to record proxy metrics: {e}")
            return False
    
    def get_provider_metrics(self, provider_id=None, days=7):
        """
        Get performance metrics for a proxy provider.
        
        Args:
            provider_id (str, optional): Provider ID, or all if None
            days (int, optional): Number of days to analyze
            
        Returns:
            dict: Provider performance metrics
        """
        if self.metrics_collection is None:
            logger.error("Database not connected")
            return {}
        
        metrics = {}
        
        try:
            # Get provider(s)
            if provider_id:
                providers = [self.proxy_service.get_provider(provider_id)]
            else:
                providers = self.proxy_service.list_providers()
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            for provider in providers:
                if not provider:
                    continue
                
                provider_name = provider.get("name")
                provider_id = str(provider.get("_id"))
                
                # Get IPs for this provider
                ips = self.ip_pool.list_ips(provider=provider_name)
                ip_ids = [str(ip.get("_id")) for ip in ips]
                
                # Query metrics for these IPs
                pipeline = [
                    {
                        "$match": {
                            "ip_id": {"$in": ip_ids},
                            "timestamp": {"$gte": start_date}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$ip_id",
                            "requests": {"$sum": 1},
                            "successes": {"$sum": {"$cond": ["$success", 1, 0]}},
                            "avg_response_time": {"$avg": "$response_time"},
                            "errors": {
                                "$push": {
                                    "$cond": [
                                        {"$eq": ["$success", False]},
                                        {
                                            "error": "$error",
                                            "url": "$request_url",
                                            "timestamp": "$timestamp"
                                        },
                                        "$$REMOVE"
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "total_requests": {"$sum": "$requests"},
                            "total_successes": {"$sum": "$successes"},
                            "avg_response_time": {"$avg": "$avg_response_time"},
                            "ip_count": {"$sum": 1},
                            "errors": {"$push": "$errors"}
                        }
                    }
                ]
                
                results = list(self.metrics_collection.aggregate(pipeline))
                
                if results:
                    result = results[0]
                    total_requests = result.get("total_requests", 0)
                    total_successes = result.get("total_successes", 0)
                    
                    success_rate = 0
                    if total_requests > 0:
                        success_rate = (total_successes / total_requests) * 100
                    
                    # Flatten errors array
                    errors = []
                    for error_group in result.get("errors", []):
                        errors.extend(error_group)
                    
                    # Get most common errors
                    error_counts = {}
                    for error in errors:
                        error_msg = error.get("error", "Unknown")
                        if error_msg in error_counts:
                            error_counts[error_msg] += 1
                        else:
                            error_counts[error_msg] = 1
                    
                    # Sort errors by count
                    common_errors = sorted(
                        [{"error": k, "count": v} for k, v in error_counts.items()],
                        key=lambda x: x["count"],
                        reverse=True
                    )[:5]  # Top 5 errors
                    
                    metrics[provider_id] = {
                        "provider_name": provider_name,
                        "total_requests": total_requests,
                        "success_rate": success_rate,
                        "avg_response_time": result.get("avg_response_time"),
                        "ip_count": result.get("ip_count", 0),
                        "common_errors": common_errors
                    }
                else:
                    metrics[provider_id] = {
                        "provider_name": provider_name,
                        "total_requests": 0,
                        "success_rate": 0,
                        "avg_response_time": 0,
                        "ip_count": len(ips),
                        "common_errors": []
                    }
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting provider metrics: {e}")
            return {}
    
    def get_ip_health(self, days=1):
        """
        Get health metrics for all IPs.
        
        Args:
            days (int, optional): Number of days to analyze
            
        Returns:
            dict: IP health metrics
        """
        if self.metrics_collection is None:
            logger.error("Database not connected")
            return {}
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Query metrics for all IPs
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$ip_id",
                        "ip_address": {"$first": "$ip_address"},
                        "provider": {"$first": "$provider"},
                        "requests": {"$sum": 1},
                        "successes": {"$sum": {"$cond": ["$success", 1, 0]}},
                        "avg_response_time": {"$avg": "$response_time"},
                        "last_used": {"$max": "$timestamp"}
                    }
                },
                {
                    "$project": {
                        "ip_address": 1,
                        "provider": 1,
                        "requests": 1,
                        "successes": 1,
                        "avg_response_time": 1,
                        "last_used": 1,
                        "success_rate": {
                            "$cond": [
                                {"$eq": ["$requests", 0]},
                                0,
                                {"$multiply": [{"$divide": ["$successes", "$requests"]}, 100]}
                            ]
                        }
                    }
                },
                {
                    "$sort": {"success_rate": -1}
                }
            ]
            
            results = list(self.metrics_collection.aggregate(pipeline))
            
            # Get current IP status
            all_ips = {str(ip.get("_id")): ip for ip in self.ip_pool.list_ips()}
            
            # Combine metrics with current status
            for result in results:
                ip_id = result.get("_id")
                if ip_id in all_ips:
                    result["status"] = all_ips[ip_id].get("status")
                    result["current_users"] = all_ips[ip_id].get("current_users")
                    result["max_users"] = all_ips[ip_id].get("max_users")
                    result["failure_count"] = all_ips[ip_id].get("failure_count")
                    result["ban_count"] = all_ips[ip_id].get("ban_count")
                else:
                    result["status"] = "unknown"
                    result["current_users"] = 0
                    result["max_users"] = 0
                    result["failure_count"] = 0
                    result["ban_count"] = 0
            
            return results
        except Exception as e:
            logger.error(f"Error getting IP health: {e}")
            return []
    
    def create_indexes(self):
        """
        Create necessary indexes for the metrics collection.
        
        Returns:
            bool: True if indexes created, False otherwise
        """
        if self.metrics_collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            # Index on IP ID for quick lookups
            self.metrics_collection.create_index("ip_id")
            
            # Index on timestamp for time-based queries
            self.metrics_collection.create_index("timestamp")
            
            # Compound index for provider and success queries
            self.metrics_collection.create_index([
                ("provider", 1),
                ("success", 1),
                ("timestamp", -1)
            ])
            
            logger.info("Created indexes for proxy metrics collection")
            return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False


class ProxyHealthCheck:
    """Checks proxy health and handles failing proxies."""
    
    def __init__(self):
        """Initialize ProxyHealthCheck."""
        self.ip_pool = IPAddress()
        self.proxy_service = ProxyService()
        self.metrics = ProxyMetrics()
    
    def check_proxy_health(self, ip_id):
        """
        Check the health of a specific proxy.
        
        Args:
            ip_id (str): The IP ID
            
        Returns:
            dict: Health check results
        """
        ip = self.ip_pool.get_ip(ip_id)
        
        if not ip:
            logger.warning(f"IP with ID {ip_id} not found")
            return {
                "success": False,
                "error": "IP not found"
            }
        
        import requests
        
        proxy_url = ip.get("proxy_url")
        username = ip.get("username")
        password = ip.get("password")
        
        if not proxy_url:
            return {
                "success": False,
                "error": "No proxy URL available"
            }
        
        # Create proxy dictionary
        proxy_dict = {}
        
        if username and password:
            auth = f"{username}:{password}@"
            if "://" in proxy_url:
                protocol, address = proxy_url.split("://", 1)
                proxy_url = f"{protocol}://{auth}{address}"
            else:
                proxy_url = f"http://{auth}{proxy_url}"
        
        proxy_dict = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # Try several test URLs
        test_urls = [
            "http://httpbin.org/ip",            # Returns IP info
            "http://httpbin.org/status/200",    # Always returns 200
            "https://www.google.com/robots.txt"  # Common stable URL
        ]
        
        results = []
        overall_success = True
        
        for url in test_urls:
            try:
                start_time = time.time()
                
                # Set a reasonable timeout
                response = requests.get(url, proxies=proxy_dict, timeout=10)
                
                response_time = time.time() - start_time
                
                results.append({
                    "url": url,
                    "success": response.status_code < 400,
                    "status_code": response.status_code,
                    "response_time": response_time
                })
                
                # Record metrics
                self.metrics.record_proxy_usage(
                    ip_id,
                    url,
                    response.status_code < 400,
                    response_time,
                    response.status_code
                )
                
                if response.status_code >= 400:
                    overall_success = False
                
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
                
                # Record failure
                self.metrics.record_proxy_usage(
                    ip_id,
                    url,
                    False,
                    error=str(e)
                )
                
                overall_success = False
        
        # Update IP status based on health check
        if not overall_success:
            self.ip_pool.report_ip_failure(
                ip_id,
                "health_check_failure",
                f"Failed health check: {results}"
            )
        
        return {
            "ip_address": ip.get("ip_address"),
            "success": overall_success,
            "tests": results
        }
    
    def check_all_proxies(self, status=None):
        """
        Check health of all proxies.
        
        Args:
            status (str, optional): Only check IPs with this status
            
        Returns:
            dict: Health check results by IP
        """
        ips = self.ip_pool.list_ips(status=status)
        results = {}
        
        for ip in ips:
            ip_id = str(ip.get("_id"))
            results[ip_id] = self.check_proxy_health(ip_id)
        
        return results
    
    def handle_failing_proxies(self, threshold=50):
        """
        Handle failing proxies based on success rate.
        
        Args:
            threshold (int, optional): Success rate threshold percentage
            
        Returns:
            dict: Actions taken
        """
        # Get IP health metrics
        ip_health = self.metrics.get_ip_health(days=1)
        
        actions = {
            "flagged": [],
            "banned": [],
            "rotated": []
        }
        
        for ip in ip_health:
            ip_id = ip.get("_id")
            success_rate = ip.get("success_rate", 0)
            
            # Skip IPs with no requests
            if ip.get("requests", 0) < 10:
                continue
            
            # Handle based on success rate
            if success_rate < threshold:
                # Get current IP status
                current_ip = self.ip_pool.get_ip(ip_id)
                
                if not current_ip:
                    continue
                
                if success_rate < 20:
                    # Very poor performance, mark as banned
                    if self.ip_pool.update_ip_status(
                        ip_id,
                        IPAddress.STATUS_BANNED,
                        f"Extremely low success rate: {success_rate}%"
                    ):
                        actions["banned"].append({
                            "ip_id": ip_id,
                            "ip_address": ip.get("ip_address"),
                            "success_rate": success_rate
                        })
                elif success_rate < 40:
                    # Poor performance, flag for review
                    if self.ip_pool.update_ip_status(
                        ip_id,
                        IPAddress.STATUS_FLAGGED,
                        f"Low success rate: {success_rate}%"
                    ):
                        actions["flagged"].append({
                            "ip_id": ip_id,
                            "ip_address": ip.get("ip_address"),
                            "success_rate": success_rate
                        })
                else:
                    # Marginal performance, rotate if in use
                    if current_ip.get("status") == IPAddress.STATUS_IN_USE:
                        if self.ip_pool.rotate_ip(ip_id):
                            actions["rotated"].append({
                                "ip_id": ip_id,
                                "ip_address": ip.get("ip_address"),
                                "success_rate": success_rate
                            })
        
        # Log actions
        logger.info(f"Proxy health handling: "
                    f"{len(actions['banned'])} banned, "
                    f"{len(actions['flagged'])} flagged, "
                    f"{len(actions['rotated'])} rotated")
        
        return actions