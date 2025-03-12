"""
MongoDB connection and management module.
"""
import pymongo
from pymongo import MongoClient
import logging
from datetime import datetime
from database.error_handler import (
    handle_connection_error, 
    handle_operation_error,
    log_database_activity
)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mongodb')

class MongoDB:
    """MongoDB connection handler for Travian Whispers."""
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
        return cls._instance
    
    @handle_connection_error
    @log_database_activity("connection")
    def connect(self, connection_string=None, db_name='whispers'):
        """
        Connect to MongoDB using the provided connection string.
        
        Args:
            connection_string (str): MongoDB connection string
            db_name (str): Database name to use
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not connection_string:
            connection_string = "mongodb+srv://whispers:eZAafCQTrjKKcZua@cluster0.9josw.mongodb.net/whispers"
        
        try:
            self.client = MongoClient(connection_string, 
                                     serverSelectionTimeoutMS=5000,
                                     connectTimeoutMS=10000,
                                     socketTimeoutMS=45000)
            # Ping the server to test connection
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            logger.info(f"Connected to MongoDB - Database: {db_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Re-raise to let the decorator handle it
            raise
    
    def get_db(self):
        """
        Get the database instance.
        
        Returns:
            pymongo.database.Database: Database instance or None if not connected
        """
        if not self.client or not self.db:
            logger.warning("Database not connected. Call connect() first.")
            return None
        return self.db
    
    def get_collection(self, collection_name):
        """
        Get a collection by name.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            pymongo.collection.Collection: Collection instance or None if not found
        """
        if not self.db:
            logger.warning("Database not connected. Call connect() first.")
            return None
        return self.db[collection_name]
    
    @handle_operation_error
    @log_database_activity("index creation")
    def create_indexes(self):
        """
        Create required indexes for all collections.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # User collection indexes
            self.db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            self.db.users.create_index([("email", pymongo.ASCENDING)], unique=True)
            self.db.users.create_index([("verificationToken", pymongo.ASCENDING)])
            self.db.users.create_index([("resetPasswordToken", pymongo.ASCENDING)])
            self.db.users.create_index([("subscription.status", pymongo.ASCENDING)])
            self.db.users.create_index([("subscription.endDate", pymongo.ASCENDING)])
            
            # Subscription plans indexes
            self.db.subscriptionPlans.create_index([("name", pymongo.ASCENDING)], unique=True)
            
            # Transactions indexes
            self.db.transactions.create_index([("userId", pymongo.ASCENDING)])
            self.db.transactions.create_index([("paymentId", pymongo.ASCENDING)], unique=True)
            self.db.transactions.create_index([("createdAt", pymongo.DESCENDING)])
            self.db.transactions.create_index([("status", pymongo.ASCENDING)])
            
            logger.info("All database indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            # Re-raise to let the decorator handle it
            raise
    
    def disconnect(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def __enter__(self):
        """Context manager enter."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

