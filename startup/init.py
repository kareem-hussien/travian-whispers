"""
Initialization module for Travian Whispers application.
This module loads and initializes all necessary components.
"""
import logging
import os
import sys
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('travian_whispers.log')
    ]
)
logger = logging.getLogger(__name__)

def init_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'browser_sessions',
        'info/profile',
        'info/maps',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def init_database():
    """Initialize database connection and collections."""
    try:
        from startup.db_config import get_db_client
        client = get_db_client()
        db = client['travian_whispers']
        
        # Create collections if they don't exist
        collections = [
            'users',
            'subscription_plans',
            'proxied_ips',
            'ip_assignments',
            'activity_logs',
            'tasks'
        ]
        
        for collection in collections:
            if collection not in db.list_collection_names():
                db.create_collection(collection)
                logger.info(f"Created collection: {collection}")
        
        # Create indexes
        db['users'].create_index('username', unique=True)
        db['users'].create_index('email', unique=True)
        db['proxied_ips'].create_index('ip', unique=True)
        db['ip_assignments'].create_index('userId', unique=True)
        
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

def init_ip_pool():
    """Initialize the IP pool with test data if empty."""
    try:
        from startup.ip_manager import IPManager
        ip_manager = IPManager()
        
        # Check if IP pool is empty
        ip_count = ip_manager.ip_collection.count_documents({})
        
        if ip_count == 0:
            logger.info("IP pool is empty, adding test IPs")
            
            # Add test IPs (these would be replaced with real proxies in production)
            test_ips = [
                {
                    "ip": "192.168.1.101",
                    "port": 8080,
                    "username": "testuser1",
                    "password": "testpass1",
                    "proxy_type": "http"
                },
                {
                    "ip": "192.168.1.102",
                    "port": 8080,
                    "username": "testuser2",
                    "password": "testpass2",
                    "proxy_type": "http"
                },
                {
                    "ip": "192.168.1.103",
                    "port": 8080,
                    "username": "testuser3",
                    "password": "testpass3",
                    "proxy_type": "http"
                }
            ]
            
            for ip_data in test_ips:
                ip_manager.add_ip(
                    ip_data["ip"],
                    ip_data["port"],
                    ip_data["username"],
                    ip_data["password"],
                    ip_data["proxy_type"]
                )
            
            logger.info(f"Added {len(test_ips)} test IPs to the pool")
        else:
            logger.info(f"IP pool already contains {ip_count} IPs")
        
        return True
    except Exception as e:
        logger.error(f"IP pool initialization error: {e}")
        return False

def start_task_runner():
    """Start the task runner."""
    try:
        from tasks.task_runner import task_runner
        
        if task_runner.start():
            logger.info("Task runner started successfully")
            return True
        else:
            logger.warning("Task runner already running or failed to start")
            return False
    except Exception as e:
        logger.error(f"Task runner initialization error: {e}")
        return False

def start_scheduled_jobs():
    """Start the scheduled job manager."""
    try:
        from startup.scheduled_jobs import scheduled_job_manager
        
        if scheduled_job_manager.start():
            logger.info("Scheduled job manager started successfully")
            return True
        else:
            logger.warning("Scheduled job manager already running or failed to start")
            return False
    except Exception as e:
        logger.error(f"Scheduled job manager initialization error: {e}")
        return False

def init_app():
    """Initialize the Flask application."""
    try:
        from app import create_app
        app = create_app()
        
        # Register IP routes
        from web.routes.ip_routes import ip_bp
        app.register_blueprint(ip_bp)
        
        logger.info("Flask application initialized successfully")
        return app
    except Exception as e:
        logger.error(f"Flask application initialization error: {e}")
        return None

def initialize_all():
    """Initialize all components."""
    logger.info("Starting Travian Whispers initialization")
    
    # Initialize directories
    init_directories()
    
    # Initialize database
    if not init_database():
        logger.error("Database initialization failed, aborting")
        return False
    
    # Initialize IP pool
    if not init_ip_pool():
        logger.warning("IP pool initialization failed, continuing anyway")
    
    # Start task runner
    if not start_task_runner():
        logger.warning("Task runner failed to start, continuing anyway")
    
    # Start scheduled jobs
    if not start_scheduled_jobs():
        logger.warning("Scheduled job manager failed to start, continuing anyway")
    
    # Initialize Flask app
    app = init_app()
    if not app:
        logger.error("Flask application initialization failed, aborting")
        return False
    
    logger.info("Travian Whispers initialization completed successfully")
    return app

# If this script is run directly, initialize everything
if __name__ == "__main__":
    initialize_all()
