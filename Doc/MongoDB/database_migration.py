#!/usr/bin/env python3
"""
Database Migration Script for Travian Whispers

This script helps migrate the database from development to production by:
1. Connecting to MongoDB
2. Creating necessary collections and indexes
3. Initializing default data
4. Removing any test/mock data
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from bson import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_migration')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database modules
from database.mongodb import MongoDB
from database.models.user import User
from database.models.subscription import SubscriptionPlan
from database.models.transaction import Transaction
from database.models.ip_pool import IPAddress
from database.models.proxy_service import ProxyService
from database.models.village import Village
from database.models.auto_farm import AutoFarm
from database.models.trainer import TroopTrainer
from database.models.activity import UserActivity
from database.models.log import ActivityLog, SystemLog
from database.models.backup import BackupRecord
from database.models.faq import FAQ
from database.settings import Settings


def connect_to_database():
    """
    Connect to MongoDB database.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    logger.info("Connecting to MongoDB...")
    
    # Initialize MongoDB connection
    db = MongoDB()
    
    try:
        connected = db.connect()
        if connected:
            logger.info("Successfully connected to MongoDB")
            return True
        else:
            logger.error("Failed to connect to MongoDB")
            return False
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return False


def create_indexes():
    """
    Create indexes for all collections.
    
    Returns:
        bool: True if all indexes were created successfully, False otherwise
    """
    logger.info("Creating database indexes...")
    
    try:
        # Create MongoDB built-in indexes
        db = MongoDB()
        success = db.create_indexes()
        
        if not success:
            logger.error("Failed to create built-in indexes")
            return False
            
        # Create model-specific indexes
        logger.info("Creating model-specific indexes...")
        
        # IP Pool indexes
        ip_model = IPAddress()
        ip_model.create_indexes()
        
        # Proxy Service indexes
        proxy_model = ProxyService()
        proxy_model.create_indexes()
        
        logger.info("All indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        return False


def initialize_default_data():
    """
    Initialize default data for the application.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logger.info("Initializing default data...")
    
    try:
        # Initialize subscription plans
        subscription_model = SubscriptionPlan()
        if subscription_model.collection.count_documents({}) == 0:
            logger.info("Creating default subscription plans...")
            subscription_model.create_default_plans()
        else:
            logger.info("Subscription plans already exist")
            
        # Initialize application settings
        settings_model = Settings()
        settings_model.initialize_default_settings()
        logger.info("Application settings initialized")
        
        # Create admin user if it doesn't exist
        user_model = User()
        admin_email = os.getenv("ADMIN_EMAIL", "admin@travianwhispers.com")
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "change-this-password")
        
        if not user_model.get_user_by_username(admin_username):
            logger.info(f"Creating admin user: {admin_username}")
            admin_user = user_model.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                role="admin"
            )
            
            if admin_user:
                # Mark admin as verified
                user_model.verify_user_by_id(str(admin_user["_id"]))
                logger.info("Admin user created and verified")
            else:
                logger.error("Failed to create admin user")
        else:
            logger.info("Admin user already exists")
            
        return True
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")
        return False


def remove_test_data():
    """
    Remove any test or mock data from the database.
    
    Returns:
        bool: True if all test data was removed successfully, False otherwise
    """
    logger.info("Removing test data...")
    
    try:
        user_model = User()
        
        # Remove test users (those with test emails)
        test_users_query = {
            "email": {"$regex": "test|example|dummy"}
        }
        
        # Exclude the admin user
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        test_users_query["username"] = {"$ne": admin_username}
        
        test_users = user_model.collection.find(test_users_query)
        test_user_ids = [str(user["_id"]) for user in test_users]
        
        if test_user_ids:
            logger.info(f"Found {len(test_user_ids)} test users to remove")
            
            # Delete test users
            for user_id in test_user_ids:
                user_model.delete_user(user_id)
                
            logger.info("Test users removed")
        else:
            logger.info("No test users found")
            
        # Remove test transactions (those with invalid plan IDs or user IDs)
        transaction_model = Transaction()
        
        # Find transactions with non-existent plan IDs
        invalid_tx_count = 0
        for tx in transaction_model.collection.find():
            # Check if user exists
            if not user_model.get_user_by_id(str(tx["userId"])):
                transaction_model.collection.delete_one({"_id": tx["_id"]})
                invalid_tx_count += 1
                
            # Check if plan exists
            subscription_model = SubscriptionPlan()
            if not subscription_model.get_plan_by_id(str(tx["planId"])):
                transaction_model.collection.delete_one({"_id": tx["_id"]})
                invalid_tx_count += 1
                
        if invalid_tx_count > 0:
            logger.info(f"Removed {invalid_tx_count} invalid transactions")
        else:
            logger.info("No invalid transactions found")
            
        # Clean up activity logs older than 90 days
        log_model = ActivityLog()
        deleted_logs = log_model.delete_logs_older_than(90)
        logger.info(f"Removed {deleted_logs} old activity logs")
        
        return True
    except Exception as e:
        logger.error(f"Error removing test data: {e}")
        return False


def verify_database_integrity():
    """
    Verify database integrity by checking for inconsistencies.
    
    Returns:
        bool: True if database integrity is verified, False if issues were found
    """
    logger.info("Verifying database integrity...")
    
    try:
        user_model = User()
        subscription_model = SubscriptionPlan()
        issues_found = False
        
        # Check if all users with active subscriptions have valid plan IDs
        users_with_subscriptions = user_model.collection.find({
            "subscription.status": "active",
            "subscription.planId": {"$ne": None}
        })
        
        for user in users_with_subscriptions:
            plan_id = user["subscription"]["planId"]
            if not subscription_model.get_plan_by_id(str(plan_id)):
                logger.warning(f"User {user['username']} has invalid plan ID: {plan_id}")
                issues_found = True
                
                # Fix: Set subscription to inactive
                user_model.update_subscription_status(str(user["_id"]), "inactive")
                logger.info(f"Fixed: Set {user['username']}'s subscription to inactive")
        
        # Check for orphaned village records
        village_model = Village()
        if hasattr(village_model, "collection") and village_model.collection is not None:
            villages = list(village_model.collection.find())
            
            for village in villages:
                user_id = village["userId"]
                if not user_model.get_user_by_id(str(user_id)):
                    logger.warning(f"Found orphaned village record for non-existent user ID: {user_id}")
                    issues_found = True
                    
                    # Fix: Delete orphaned village
                    village_model.collection.delete_one({"_id": village["_id"]})
                    logger.info(f"Fixed: Deleted orphaned village {village['name']}")
        
        if issues_found:
            logger.warning("Database integrity issues were found and fixed")
        else:
            logger.info("Database integrity verified, no issues found")
            
        return True
    except Exception as e:
        logger.error(f"Error verifying database integrity: {e}")
        return False


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Database Migration Tool for Travian Whispers")
    parser.add_argument("--connect-only", action="store_true", help="Only test database connection")
    parser.add_argument("--indexes", action="store_true", help="Create database indexes")
    parser.add_argument("--init-data", action="store_true", help="Initialize default data")
    parser.add_argument("--clean", action="store_true", help="Remove test/mock data")
    parser.add_argument("--verify", action="store_true", help="Verify database integrity")
    parser.add_argument("--all", action="store_true", help="Perform all operations")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # Connecting to database is required for all operations
    if not connect_to_database():
        logger.error("Cannot proceed without database connection")
        sys.exit(1)
        
    if args.connect_only:
        logger.info("Database connection test completed successfully")
        sys.exit(0)
        
    # Perform requested operations
    if args.all or args.indexes:
        if not create_indexes():
            logger.error("Failed to create indexes")
            sys.exit(1)
            
    if args.all or args.init_data:
        if not initialize_default_data():
            logger.error("Failed to initialize default data")
            sys.exit(1)
            
    if args.all or args.clean:
        if not remove_test_data():
            logger.error("Failed to remove test data")
            sys.exit(1)
            
    if args.all or args.verify:
        if not verify_database_integrity():
            logger.error("Failed to verify database integrity")
            sys.exit(1)
            
    logger.info("Database migration completed successfully")
    

if __name__ == "__main__":
    main()