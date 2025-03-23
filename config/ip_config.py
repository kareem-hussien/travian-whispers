"""
IP Configuration module for Travian Whispers application.
This module contains configuration settings for IP management and rotation.
"""
import os
from datetime import timedelta

# IP Pool Settings
IP_POOL_SIZE_MIN = int(os.environ.get('IP_POOL_SIZE_MIN', 10))  # Minimum number of IPs in the pool
IP_POOL_SIZE_MAX = int(os.environ.get('IP_POOL_SIZE_MAX', 100))  # Maximum number of IPs in the pool
IP_POOL_SIZE_TARGET = int(os.environ.get('IP_POOL_SIZE_TARGET', 25))  # Target number of IPs in the pool

# IP Assignment Settings
IP_MAX_USERS_PER_IP = int(os.environ.get('IP_MAX_USERS_PER_IP', 1))  # Maximum users per IP
IP_RESERVE_PERCENTAGE = int(os.environ.get('IP_RESERVE_PERCENTAGE', 20))  # Percentage of IPs to keep in reserve

# IP Rotation Settings
IP_ROTATION_INTERVAL = int(os.environ.get('IP_ROTATION_INTERVAL', 30))  # Default rotation interval in minutes
IP_COOLDOWN_MINUTES = int(os.environ.get('IP_COOLDOWN_MINUTES', 30))  # Cooldown period after rotation
IP_ROTATION_STRATEGIES = ['time_based', 'activity_based', 'pattern_based', 'random']  # Available rotation strategies
IP_DEFAULT_ROTATION_STRATEGY = os.environ.get('IP_DEFAULT_ROTATION_STRATEGY', 'time_based')  # Default strategy

# IP Health and Monitoring
IP_FAILURE_THRESHOLD = int(os.environ.get('IP_FAILURE_THRESHOLD', 5))  # Failures before IP is flagged
IP_BAN_THRESHOLD = int(os.environ.get('IP_BAN_THRESHOLD', 2))  # Bans before IP is removed from pool
IP_HEALTH_CHECK_INTERVAL = int(os.environ.get('IP_HEALTH_CHECK_INTERVAL', 6))  # Health check interval in hours
IP_HIGH_ACTIVITY_THRESHOLD = int(os.environ.get('IP_HIGH_ACTIVITY_THRESHOLD', 100))  # Requests per hour for "high activity"

# Session Settings
SESSION_DIR = os.environ.get('SESSION_DIR', 'browser_sessions')  # Directory for browser sessions
SESSION_MAX_AGE = int(os.environ.get('SESSION_MAX_AGE', 24))  # Maximum session age in hours
SESSION_ROTATION_AFTER_DETECTION = bool(int(os.environ.get('SESSION_ROTATION_AFTER_DETECTION', 1)))  # Rotate after detection

# Detection Settings
DETECTION_RISK_LEVELS = ['low', 'medium', 'high']  # Risk levels for detection events
DETECTION_RESPONSE_STRATEGIES = {
    'low': 'monitor',  # Just monitor and log
    'medium': 'session_rotation',  # Rotate browser session only
    'high': 'full_rotation'  # Rotate both IP and session
}

# Proxy Provider Settings
PROXY_PROVIDERS = {
    'brightdata': {
        'enabled': bool(int(os.environ.get('PROXY_BRIGHTDATA_ENABLED', 0))),
        'api_key': os.environ.get('PROXY_BRIGHTDATA_API_KEY', ''),
        'username': os.environ.get('PROXY_BRIGHTDATA_USERNAME', ''),
        'password': os.environ.get('PROXY_BRIGHTDATA_PASSWORD', ''),
        'zone': os.environ.get('PROXY_BRIGHTDATA_ZONE', ''),
        'port': os.environ.get('PROXY_BRIGHTDATA_PORT', '22225'),
        'endpoint': os.environ.get('PROXY_BRIGHTDATA_ENDPOINT', 'https://api.brightdata.com/zone/ips')
    },
    'oxylabs': {
        'enabled': bool(int(os.environ.get('PROXY_OXYLABS_ENABLED', 0))),
        'api_key': os.environ.get('PROXY_OXYLABS_API_KEY', ''),
        'username': os.environ.get('PROXY_OXYLABS_USERNAME', ''),
        'password': os.environ.get('PROXY_OXYLABS_PASSWORD', ''),
        'endpoint': os.environ.get('PROXY_OXYLABS_ENDPOINT', 'https://api.oxylabs.io/v1/proxies')
    },
    'smartproxy': {
        'enabled': bool(int(os.environ.get('PROXY_SMARTPROXY_ENABLED', 0))),
        'api_key': os.environ.get('PROXY_SMARTPROXY_API_KEY', ''),
        'username': os.environ.get('PROXY_SMARTPROXY_USERNAME', ''),
        'password': os.environ.get('PROXY_SMARTPROXY_PASSWORD', ''),
        'endpoint': os.environ.get('PROXY_SMARTPROXY_ENDPOINT', 'https://api.smartproxy.com/v1/endpoints')
    }
}

# Subscription Plan IP Limits
SUBSCRIPTION_IP_LIMITS = {
    'basic': 2,      # Basic tier: 2 IPs
    'standard': 5,   # Standard tier: 5 IPs 
    'premium': 10    # Premium tier: 10 IPs
}

# Geographic IP Distribution Settings
GEO_MATCHING_ENABLED = bool(int(os.environ.get('GEO_MATCHING_ENABLED', 0)))  # Enable geographic IP matching
GEO_DEFAULT_COUNTRY = os.environ.get('GEO_DEFAULT_COUNTRY', 'US')  # Default country code
GEO_DATABASE_PATH = os.environ.get('GEO_DATABASE_PATH', 'utils/geo_ip_db.mmdb')  # Path to MaxMind GeoIP database

def get_subscription_ip_limit(plan_name):
    """
    Get the IP limit for a subscription plan.
    
    Args:
        plan_name (str): Name of the subscription plan
        
    Returns:
        int: Maximum number of IPs for the plan
    """
    plan_name = plan_name.lower() if plan_name else 'basic'
    return SUBSCRIPTION_IP_LIMITS.get(plan_name, SUBSCRIPTION_IP_LIMITS['basic'])

def get_rotation_interval_for_risk(risk_level):
    """
    Get rotation interval for a risk level.
    
    Args:
        risk_level (str): Risk level (low, medium, high)
        
    Returns:
        timedelta: Rotation interval as timedelta
    """
    if risk_level == 'high':
        return timedelta(minutes=0)  # Immediate rotation
    elif risk_level == 'medium':
        return timedelta(minutes=5)  # Rotate after 5 minutes
    else:  # low or unknown
        return timedelta(minutes=IP_ROTATION_INTERVAL)  # Use default interval
