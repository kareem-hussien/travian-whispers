#!/usr/bin/env python3
"""
Travian Whispers - Advanced Travian Automation Suite
Main entry point for both the web application and the bot.

Author: Eng. Kareem Hussien
Contact: https://wa.me/00201099339393
"""
import warnings
warnings.filterwarnings(
    "ignore", 
    message="Unable to find acceptable character detection dependency", 
    module="requests"
)

import os
import sys
import time
import logging
import argparse
import threading
import traceback
import datetime
from pathlib import Path
from startup.ip_manager import IPManager
from utils.proxy_metrics import ProxyHealthCheck

ip_manager = IPManager()
ip_manager.initialize()

# Create indexes
proxy_metrics = ProxyMetrics()
proxy_metrics.create_indexes()

# Initial health check
proxy_health = ProxyHealthCheck()
app.ip_manager = ip_manager
app.proxy_health = proxy_health

# Load environment variables if .env file exists
try:
    from dotenv import load_dotenv
    env_path = Path(".") / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print("[INFO] Loaded environment variables from .env file")
except ImportError:
    print("[WARNING] dotenv package not installed. Environment variables must be set manually.")

# Configure logging
log_directory = Path("logs")
log_directory.mkdir(exist_ok=True)
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_filename = log_directory / f"travian_whispers_{current_date}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename)
    ]
)
logger = logging.getLogger('main')

# Check if running in a virtual environment
def in_virtualenv():
    """Check if running inside a virtual environment."""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

if not in_virtualenv():
    logger.warning("Not running in a virtual environment! It's recommended to use a venv.")

# Import signal handler (don't fail if the file doesn't exist yet)
try:
    from signal_handler import initialize_signal_handlers, register_shutdown_handler
    has_signal_handler = True
except ImportError:
    logger.warning("Signal handler not available. Graceful shutdown may be limited.")
    has_signal_handler = False

# Import cron jobs (don't fail if the file doesn't exist yet)
try:
    from cron_jobs import start_scheduler
    has_scheduler = True
except ImportError:
    logger.warning("Cron jobs scheduler not available. Scheduled tasks will not run.")
    has_scheduler = False

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Travian Whispers - Advanced Travian Automation Suite',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--web', action='store_true', help='Run in web application mode')
    parser.add_argument('--user-id', help='User ID for authentication in bot mode')
    parser.add_argument('--setup', action='store_true', help='Run setup procedure')
    parser.add_argument('--check-imports', action='store_true', help='Check Python imports')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--host', default='0.0.0.0', help='Host address for web mode')
    parser.add_argument('--port', type=int, default=5000, help='Port for web mode')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    return parser.parse_args()

def setup_mode():
    """
    Run setup script to initialize the project.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Running setup procedure...")
        
        # Try to import setup module
        try:
            from setup import main as setup_main
            return setup_main()
        except ImportError:
            # If setup.py doesn't exist yet, create base directories
            logger.warning("Setup module not found. Creating basic directory structure...")
            
            # Create directories
            directories = [
                "database", "database/models", "auth", "email_module", "email_module/templates",
                "payment", "web", "web/static", "web/static/css", "web/static/js", "web/static/img",
                "web/templates", "web/templates/errors", "web/templates/user", "web/templates/admin",
                "startup", "tasks", "tasks/trainer", "info", "info/maps", "info/profile",
                "logs", "backups"
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            
            # Create __init__.py files
            for directory in directories:
                if "/" in directory:  # Only create in subdirectories
                    init_file = os.path.join(directory, "__init__.py")
                    if not os.path.exists(init_file):
                        with open(init_file, "w") as f:
                            f.write('"""Package initialization."""\n')
                        logger.info(f"Created: {init_file}")
            
            logger.info("Basic directory structure created successfully!")
            return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        logger.error(traceback.format_exc())
        return 1

def check_imports_mode():
    """
    Run import checker script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("Checking Python imports...")
    
    try:
        # Try to import check_imports module
        try:
            from check_imports import main as check_imports_main
            return check_imports_main()
        except ImportError:
            logger.error("Import checker script not found.")
            logger.info("You can create a check_imports.py file to verify your Python imports.")
            return 1
    except Exception as e:
        logger.error(f"Import checking failed: {e}")
        logger.error(traceback.format_exc())
        return 1

def web_mode(host='0.0.0.0', port=5000, debug=False):
    """
    Run in web application mode.
    """
    try:
        # Connect to database
        try:
            from database.mongodb import MongoDB
            db = MongoDB()
            if not db.connect():
                logger.error("Failed to connect to MongoDB. Please check your connection string.")
                return 1
            logger.info("Connected to MongoDB successfully.")
        except ImportError:
            logger.warning("MongoDB module not found. Database functionality will be limited.")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            logger.error(traceback.format_exc())
            return 1
        
        # Import and run Flask application
        try:
            from web.app import create_app  # Import the factory function
            app = create_app()  # Create the app instance
            
            # Set debug mode based on argument
            app.config['DEBUG'] = debug
            
            # Get host and port from environment variables or use provided values
            env_host = os.environ.get('HOST', host)
            env_port = int(os.environ.get('PORT', port))
            
            logger.info(f"Starting web server on {env_host}:{env_port} (debug={debug})")
            app.run(host=env_host, port=env_port, debug=debug)
            return 0
        except ImportError as e:
            logger.error(f"Failed to import web application: {e}")
            logger.error("Make sure the web module is properly installed.")
            return 1
    except Exception as e:
        logger.error(f"Error in web mode: {e}")
        logger.error(traceback.format_exc())
        return 1

# File: main.py (Update bot_mode function)

def bot_mode(user_id=None, headless=False):
    """
    Run in bot mode for automating Travian.
    
    Args:
        user_id (str, optional): User ID for authentication
        headless (bool): Whether to run browser in headless mode
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Import required modules
        from utils.selenium_handler import SeleniumHandler
        from startup.welcome_messages import welcome
        from startup.tasks import run_task_menu
        
        # Ensure database is connected
        from database.mongodb import MongoDB
        db = MongoDB()
        if not db.connect():
            logger.error("Failed to connect to MongoDB. Exiting.")
            return 1
        logger.info("MongoDB connected successfully.")
        
        # Display welcome messages
        welcome()
        
        # Verify user authentication if user_id is provided
        if user_id:
            from database.models.user import User
            user_model = User()
            user = user_model.get_user_by_id(user_id)
            
            if not user:
                logger.error(f"User not found with ID: {user_id}")
                return 1
            
            logger.info(f"Authenticated as user: {user['username']}")
            
            # Check subscription
            if user['subscription']['status'] != 'active':
                logger.error("No active subscription found. Please subscribe through the web interface.")
                return 1
            
            # Get Travian credentials
            travian_username = user['travianCredentials'].get('username')
            travian_password = user['travianCredentials'].get('password')
            travian_server = user['travianCredentials'].get('server', 'https://ts1.x1.international.travian.com')
            
            if not travian_username or not travian_password:
                logger.error("Travian credentials not found. Please update your profile through the web interface.")
                return 1
        else:
            # No user_id provided, prompt for login
            try:
                from auth.login import login_user
                username_or_email = input("Enter your Travian Whispers username or email: ")
                password = input("Enter your Travian Whispers password: ")
                
                success, message, _, user_data = login_user(username_or_email, password)
                
                if not success:
                    logger.error(f"Authentication failed: {message}")
                    return 1
                
                user_id = user_data["id"]
                logger.info(f"Authentication successful. User ID: {user_id}")
                
                # Get user data
                from database.models.user import User
                user_model = User()
                user = user_model.get_user_by_id(user_id)
                
                if not user:
                    logger.error("User not found. Exiting.")
                    return 1
                
                # Check subscription
                if user['subscription']['status'] != 'active':
                    logger.error("No active subscription found. Please subscribe through the web interface.")
                    return 1
                
                # Get Travian credentials
                travian_username = user['travianCredentials'].get('username')
                travian_password = user['travianCredentials'].get('password')
                travian_server = user['travianCredentials'].get('server', 'https://ts1.x1.international.travian.com')
                
                if not travian_username or not travian_password:
                    logger.error("Travian credentials not found. Please update your profile through the web interface.")
                    return 1
            except ImportError:
                # Fallback for development: ask for Travian credentials directly
                logger.warning("Auth module not found. Using direct Travian login (development mode).")
                travian_username = input("Enter your Travian username: ")
                travian_password = input("Enter your Travian password: ")
                travian_server = input("Enter Travian server URL [https://ts1.x1.international.travian.com]: ")
                if not travian_server:
                    travian_server = "https://ts1.x1.international.travian.com"
        
        # Create Selenium handler and setup browser
        selenium_handler = SeleniumHandler()
        driver = selenium_handler.create_driver(user_id=user_id, headless=headless)
        
        # Login to Travian
        from startup.browser_profile import login_only
        if not login_only(driver, travian_username, travian_password, travian_server):
            logger.error("Failed to login to Travian. Please check your credentials.")
            driver.quit()
            return 1
        
        # Check if user needs profile update
        update_choice = input("Do you want to update your profile (check account tribe and refresh villages)? (y/n): ").strip().lower()
        if update_choice == "y":
            # Update tribe information
            from startup.browser_profile import update_profile
            profile_info = update_profile(driver)
            if profile_info:
                detected_tribe, profile_id = profile_info
                logger.info(f"Tribe detected: {detected_tribe}, Profile ID: {profile_id}")
                
                # Save to user profile in MongoDB if user_id is available
                if user_id:
                    user_model.update_travian_credentials(
                        user_id=user_id,
                        travian_username=travian_username,
                        travian_password=travian_password,
                        tribe=detected_tribe,
                        profile_id=profile_id,
                        server=travian_server
                    )
                    logger.info("Tribe and profile ID saved to user profile.")
            else:
                logger.info("Profile update failed or not confirmed.")
            
            # Refresh villages list
            refresh = input("Do you want to refresh the villages list? (y/n): ").strip().lower()
            if refresh == "y":
                logger.info("Refreshing villages list...")
                from startup.villages_list import run_villages
                villages = run_villages(driver, return_villages=True)
                
                if villages and user_id:
                    # Save villages to user profile in MongoDB
                    user_model.update_villages(user_id, villages)
                    logger.info("Villages list saved to user profile.")
                elif not villages:
                    logger.warning("Failed to refresh villages list.")
            else:
                logger.info("Skipping villages refresh. Using existing data.")
        else:
            logger.info("Skipping profile update.")
        
        # Get user settings from MongoDB if user_id is available
        max_villages = 2  # Default value
        max_tasks = 1     # Default value
        available_features = ["Auto-Farm"]  # Default value
        
        if user_id:
            # Get user settings from MongoDB
            settings = user.get('settings', {})
            
            # Get subscription limitations
            try:
                from database.models.subscription import SubscriptionPlan
                plan_model = SubscriptionPlan()
                plan = plan_model.get_plan_by_id(user['subscription']['planId'])
                
                if plan:
                    features = plan.get('features', {})
                    max_villages = features.get('maxVillages', 2)
                    max_tasks = features.get('maxTasks', 1)
                    
                    # Check available features
                    available_features = []
                    if features.get('autoFarm', True):
                        available_features.append("Auto-Farm")
                    if features.get('trainer', False):
                        available_features.append("Trainer")
                    
                    logger.info(f"Available features: {', '.join(available_features)}")
                    logger.info(f"Subscription limits: Max villages: {max_villages}, Max tasks: {max_tasks}")
            except Exception as e:
                logger.warning(f"Failed to get subscription details: {e}")
                logger.warning("Using default feature set.")
        
        # Run task menu with subscription limits
        try:
            if user_id:
                run_task_menu(
                    driver, 
                    user_id=user_id,
                    max_tasks=max_tasks,
                    available_features=available_features
                )
            else:
                # Development mode: no user_id
                run_task_menu(driver)
        except Exception as e:
            logger.error(f"Error in task menu: {e}")
            logger.error(traceback.format_exc())
            driver.quit()
            return 1
        
        # Properly close the driver when done
        driver.quit()
        
        return 0
    except Exception as e:
        logger.error(f"Error in bot mode: {e}")
        logger.error(traceback.format_exc())
        return 1

def main():
    """
    Main entry point. Parse arguments and run in the appropriate mode.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Run in the appropriate mode
    try:
        if args.setup:
            return setup_mode()
        elif args.check_imports:
            return check_imports_mode()
        elif args.web:
            return web_mode(args.host, args.port, args.debug)
        else:
            return bot_mode(args.user_id, args.headless)
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")
        return 0
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        logger.critical(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
