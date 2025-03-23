# IP Rotation & Management System Setup Guide

This guide covers the installation, configuration, and initial setup of the IP Rotation & Management System for Travian Whispers.

## Prerequisites

Before setting up the IP Rotation system, ensure you have the following prerequisites:

1. Python 3.8+ installed
2. MongoDB 4.0+ installed and running
3. Access to proxy providers for IP sourcing
4. Basic understanding of Travian Whispers architecture

## Installation

### 1. Install Required Packages

```bash
pip install -r requirements.txt
```

Make sure the following packages are included in your `requirements.txt`:

```
selenium==4.1.0
webdriver-manager==3.5.2
pymongo==4.1.1
requests==2.27.1
beautifulsoup4==4.10.0
flask==2.0.1
passlib==1.7.4
geoip2==4.5.0  # Optional for advanced geolocation
```

### 2. Install MongoDB (if not already installed)

#### For Ubuntu/Debian:

```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -

# Create list file for MongoDB
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list

# Reload package database
sudo apt-get update

# Install MongoDB packages
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod

# Enable MongoDB to start on boot
sudo systemctl enable mongod
```

#### For macOS (using Homebrew):

```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### 3. Create Required Directories

```bash
mkdir -p browser_sessions
mkdir -p info/profile
mkdir -p info/maps
mkdir -p logs
```

### 4. Configure Environment Variables

Create a `.env` file in your project root:

```
# Database settings
MONGODB_URI=mongodb://localhost:27017/whispers
MONGODB_DB_NAME=whispers
MONGODB_USERNAME=
MONGODB_PASSWORD=

# IP Pool settings
IP_POOL_SIZE_MIN=10
IP_POOL_SIZE_TARGET=25
IP_ROTATION_INTERVAL=30
IP_COOLDOWN_MINUTES=30
IP_DEFAULT_ROTATION_STRATEGY=time_based

# Proxy providers (enable as needed)
PROXY_BRIGHTDATA_ENABLED=0
PROXY_OXYLABS_ENABLED=0
PROXY_SMARTPROXY_ENABLED=0

# Session settings
SESSION_DIR=browser_sessions
SESSION_MAX_AGE=24

# Geolocation settings
GEO_MATCHING_ENABLED=0
GEO_DEFAULT_COUNTRY=US
```

Load these environment variables in your application startup code:

```python
# In your startup/init.py or similar file
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
```

## Configuration

### 1. Configure IP Pool

You have several options for setting up your IP pool:

#### Option 1: Manual IP Configuration

Add IPs manually through the admin interface or using the API:

```python
from startup.ip_manager import IPManager

ip_manager = IPManager()

# Add an IP manually
ip_manager.add_ip(
    "192.168.1.1",    # IP address
    8080,             # Port
    "username",       # Proxy username (if required)
    "password",       # Proxy password (if required)
    "http"            # Proxy type
)
```

#### Option 2: Configure Proxy Providers

Set up integration with proxy providers by editing the `.env` file:

```
# Brightdata configuration
PROXY_BRIGHTDATA_ENABLED=1
PROXY_BRIGHTDATA_API_KEY=your_api_key
PROXY_BRIGHTDATA_USERNAME=your_username
PROXY_BRIGHTDATA_PASSWORD=your_password
PROXY_BRIGHTDATA_ZONE=your_zone
PROXY_BRIGHTDATA_PORT=22225

# Oxylabs configuration
PROXY_OXYLABS_ENABLED=1
PROXY_OXYLABS_API_KEY=your_api_key
PROXY_OXYLABS_USERNAME=your_username
PROXY_OXYLABS_PASSWORD=your_password
```

Then use the proxy service to fetch IPs automatically:

```python
from database.models.proxy_service import ProxyService

proxy_service = ProxyService()

# Get provider by name
provider = proxy_service.get_provider_by_name("brightdata")

# Fetch proxies
proxies = proxy_service.fetch_proxies(
    str(provider["_id"]),
    country_code="US",
    count=10,
    update_pool=True
)
```

### 2. Configure MongoDB Indexes

Ensure the necessary indexes are created for optimal performance:

```python
from database.models.ip_pool import IPAddress
from database.models.proxy_service import ProxyService
from database.models.user_activity import UserActivity

# Create indexes for IP Pool
ip_pool = IPAddress()
ip_pool.create_indexes()

# Create indexes for Proxy Service
proxy_service = ProxyService()
proxy_service.create_indexes()

# Create indexes for User Activity
activity_model = UserActivity()
activity_model.create_indexes()
```

### 3. Configure GeoIP (Optional)

For advanced geolocation features, download and configure the MaxMind GeoIP database:

```bash
# Create directory for GeoIP database
mkdir -p utils/geoip

# Download MaxMind database (requires a MaxMind account)
cd utils/geoip
wget -O GeoLite2-City.tar.gz "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=YOUR_LICENSE_KEY&suffix=tar.gz"
tar -xzf GeoLite2-City.tar.gz
mv GeoLite2-City_*/GeoLite2-City.mmdb ./geo_ip_db.mmdb
rm -rf GeoLite2-City_*
rm GeoLite2-City.tar.gz
```

Update your `.env` file:

```
GEO_MATCHING_ENABLED=1
GEO_DATABASE_PATH=utils/geoip/geo_ip_db.mmdb
```

## Initial Setup

### 1. Start the IP Rotation Scheduler

Add the following code to your application initialization:

```python
from tasks.ip_rotation import ip_rotation_scheduler

# Start the IP rotation scheduler
ip_rotation_scheduler.start()
```

### 2. Initialize Default Proxy Providers

```python
from database.models.proxy_service import ProxyService

proxy_service = ProxyService()

# Add Brightdata provider if not exists
if not proxy_service.get_provider_by_name("brightdata"):
    proxy_service.add_provider(
        name="brightdata",
        provider_type=ProxyService.PROVIDER_BRIGHTDATA,
        api_key=os.environ.get("PROXY_BRIGHTDATA_API_KEY"),
        username=os.environ.get("PROXY_BRIGHTDATA_USERNAME"),
        password=os.environ.get("PROXY_BRIGHTDATA_PASSWORD"),
        endpoint=os.environ.get("PROXY_BRIGHTDATA_ENDPOINT"),
        config={
            "zone": os.environ.get("PROXY_BRIGHTDATA_ZONE"),
            "port": os.environ.get("PROXY_BRIGHTDATA_PORT"),
            "max_users_per_ip": 1
        }
    )
    
# Add Oxylabs provider if not exists
if not proxy_service.get_provider_by_name("oxylabs"):
    proxy_service.add_provider(
        name="oxylabs",
        provider_type=ProxyService.PROVIDER_OXYLABS,
        api_key=os.environ.get("PROXY_OXYLABS_API_KEY"),
        username=os.environ.get("PROXY_OXYLABS_USERNAME"),
        password=os.environ.get("PROXY_OXYLABS_PASSWORD"),
        endpoint=os.environ.get("PROXY_OXYLABS_ENDPOINT"),
        config={
            "port": os.environ.get("PROXY_OXYLABS_PORT"),
            "max_users_per_ip": 1
        }
    )
```

### 3. Register IP Routes

Update your Flask app to include the IP routes:

```python
# In your web/app.py or similar file
from web.routes.ip_routes import ip_bp

# Register blueprint
app.register_blueprint(ip_bp)
```

### 4. Fetch Initial IP Pool

```python
from database.models.proxy_service import ProxyService
from startup.ip_manager import IPManager

proxy_service = ProxyService()
ip_manager = IPManager()

# Check if IP pool is empty
ip_count = ip_manager.ip_collection.count_documents({})

if ip_count < int(os.environ.get("IP_POOL_SIZE_MIN", 10)):
    print("IP pool below minimum size, fetching IPs...")
    
    # Get active providers
    providers = proxy_service.list_providers(active_only=True)
    
    if not providers:
        print("No active proxy providers configured!")
    else:
        # Calculate how many IPs to fetch per provider
        target_size = int(os.environ.get("IP_POOL_SIZE_TARGET", 25))
        ips_needed = target_size - ip_count
        ips_per_provider = max(1, ips_needed // len(providers))
        
        # Fetch IPs from each provider
        total_fetched = 0
        for provider in providers:
            provider_id = str(provider["_id"])
            proxies = proxy_service.fetch_proxies(
                provider_id=provider_id,
                count=ips_per_provider,
                update_pool=True
            )
            
            if proxies:
                print(f"Fetched {len(proxies)} IPs from {provider['name']}")
                total_fetched += len(proxies)
        
        print(f"Total IPs fetched: {total_fetched}")
```

## Testing the Setup

### 1. Test IP Assignment

Create a simple test script:

```python
# test_ip_assignment.py
from startup.ip_manager import IPManager

def test_ip_assignment():
    ip_manager = IPManager()
    
    # Create test user IDs
    test_users = ["test_user_1", "test_user_2", "test_user_3"]
    
    # Clear existing assignments
    for user_id in test_users:
        ip_manager.release_ip_for_user(user_id)
    
    # Assign IPs to each test user
    assigned_ips = {}
    for user_id in test_users:
        ip_data = ip_manager.get_ip_for_user(user_id)
        if ip_data:
            assigned_ips[user_id] = ip_data["ip"]
            print(f"Assigned IP {ip_data['ip']} to user {user_id}")
        else:
            print(f"Failed to assign IP to user {user_id}")
    
    # Verify unique assignments
    unique_ips = set(assigned_ips.values())
    if len(unique_ips) == len(assigned_ips):
        print("SUCCESS: All users have unique IPs")
    else:
        print("FAILURE: Not all users have unique IPs")
    
    # Release IPs
    for user_id in test_users:
        if ip_manager.release_ip_for_user(user_id):
            print(f"Released IP for user {user_id}")
        else:
            print(f"No IP to release for user {user_id}")

if __name__ == "__main__":
    test_ip_assignment()
```

Run the test:

```bash
python test_ip_assignment.py
```

### 2. Test Browser Isolation

Create a test script for browser isolation:

```python
# test_browser_isolation.py
from startup.browser_profile import setup_browser

def test_browser_isolation():
    # Set up browsers for three test users
    drivers = {}
    test_users = ["test_user_1", "test_user_2", "test_user_3"]
    
    try:
        for user_id in test_users:
            print(f"Setting up browser for {user_id}...")
            driver = setup_browser(user_id)
            drivers[user_id] = driver
            
            # Navigate to IP checking site
            driver.get("https://www.whatismyip.com/")
            print(f"Browser for {user_id} navigated to IP check site")
            
        # Keep browsers open for manual inspection
        input("Press Enter to close all browsers...")
    finally:
        # Close all browsers
        for user_id, driver in drivers.items():
            try:
                driver.quit()
                print(f"Closed browser for {user_id}")
            except:
                pass

if __name__ == "__main__":
    test_browser_isolation()
```

Run the test:

```bash
python test_browser_isolation.py
```

### 3. Test Rotation

Create a test script for IP rotation:

```python
# test_rotation.py
from startup.ip_manager import IPManager
import time

def test_ip_rotation():
    ip_manager = IPManager()
    user_id = "test_user_rotation"
    
    # Initial IP assignment
    initial_ip = ip_manager.get_ip_for_user(user_id)
    if initial_ip:
        print(f"Initial IP assigned: {initial_ip['ip']}")
    else:
        print("Failed to assign initial IP")
        return
    
    # Wait briefly
    time.sleep(2)
    
    # Rotate IP
    new_ip = ip_manager.rotate_ip_for_user(user_id)
    if new_ip:
        print(f"Rotated to new IP: {new_ip['ip']}")
        if new_ip['ip'] != initial_ip['ip']:
            print("SUCCESS: IP was rotated successfully")
        else:
            print("FAILURE: Same IP was assigned after rotation")
    else:
        print("Failed to rotate IP")
    
    # Clean up
    ip_manager.release_ip_for_user(user_id)
    print("Test complete. IP released.")

if __name__ == "__main__":
    test_ip_rotation()
```

Run the test:

```bash
python test_rotation.py
```

## Common Issues and Solutions

### 1. No Available IPs

If you see "No available IPs for user" errors:

1. Check your proxy provider configuration
2. Ensure your API keys are valid
3. Manually add test IPs if needed:

```python
from startup.ip_manager import IPManager

ip_manager = IPManager()

# Add test IPs
for i in range(1, 11):
    ip_manager.add_ip(
        f"192.168.1.{i}",  # Test IP
        8080,              # Port
        "testuser",        # Username
        "testpass",        # Password
        "http"             # Proxy type
    )
```

### 2. MongoDB Connection Issues

If you encounter MongoDB connection problems:

1. Verify MongoDB is running: `sudo systemctl status mongod`
2. Check your connection string in `.env`
3. Ensure no firewall is blocking the connection

### 3. Browser Setup Failures

If browser setup fails:

1. Ensure Chrome and ChromeDriver are correctly installed
2. Check that the session directory exists and has proper permissions
3. Verify proxy configuration is correct

## Production Deployment Considerations

### 1. Use Environment Variables

Store all sensitive information in environment variables rather than hardcoding in files.

### 2. Regular Database Backups

Set up regular backups of your MongoDB database:

```bash
# Create backup directory
mkdir -p backups

# Add to crontab
crontab -e

# Add this line for daily backups at 3 AM
0 3 * * * mongodump --uri="mongodb://localhost:27017/whispers" --out=/path/to/app/backups/$(date +\%Y\%m\%d)
```

### 3. Monitoring

Set up monitoring for your IP pool health:

```python
from database.models.ip_pool import IPAddress
import logging

def monitor_ip_pool_health():
    ip_pool = IPAddress()
    
    # Count IPs by status
    total_ips = ip_pool.collection.count_documents({})
    available_ips = ip_pool.collection.count_documents({"status": "available", "inUse": False})
    in_use_ips = ip_pool.collection.count_documents({"inUse": True})
    banned_ips = ip_pool.collection.count_documents({"status": "banned"})
    flagged_ips = ip_pool.collection.count_documents({"status": "flagged"})
    
    # Log health status
    logging.info(f"IP Pool Health: {available_ips}/{total_ips} available, {in_use_ips} in use, {banned_ips} banned, {flagged_ips} flagged")
    
    # Alert if available IPs below threshold
    min_threshold = int(os.environ.get("IP_POOL_SIZE_MIN", 10))
    if available_ips < min_threshold:
        logging.warning(f"IP Pool Alert: Available IPs ({available_ips}) below minimum threshold ({min_threshold})")
        
        # Trigger auto-fetch
        from database.models.proxy_service import ProxyService
        proxy_service = ProxyService()
        proxy_service.auto_fetch_proxies(min_available=min_threshold)
```

### 4. Scaling Considerations

For larger deployments:

1. Use a MongoDB replica set for database redundancy
2. Implement connection pooling for MongoDB
3. Consider containerizing the application with Docker
4. Use a process manager like PM2 or Supervisor

## Next Steps

After completing the setup:

1. Configure the system for each user based on their subscription plan
2. Set up regular IP rotation schedules
3. Implement monitoring and alerting
4. Test the system with real Travian activity

By following this guide, you should have a fully functional IP Rotation & Management System that will help prevent account bans and provide a seamless experience for Travian Whispers users.
