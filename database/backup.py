"""
Database backup utility for Travian Whispers.
"""
import os
import logging
import subprocess
import datetime
import json
from pathlib import Path
import shutil
import tarfile
import gzip
from database.mongodb import MongoDB
from flask import current_app

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database.backup')

class BackupError(Exception):
    """Base class for backup-related errors."""
    def __init__(self, message, original_error=None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

def create_backup_directory(base_path="backups"):
    """
    Create a directory for storing backups.
    
    Args:
        base_path (str): Base directory for backups
        
    Returns:
        Path: Path to the created directory
    """
    try:
        backup_dir = Path(base_path)
        backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Create a timestamped subdirectory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / timestamp
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Created backup directory: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup directory: {e}")
        raise BackupError(f"Failed to create backup directory: {e}", e)

def backup_using_mongodump(connection_string, output_path, db_name="whispers"):
    """
    Create a backup using mongodump utility.
    
    Args:
        connection_string (str): MongoDB connection string
        output_path (Path): Directory to store the backup
        db_name (str): Database name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if mongodump is available
        try:
            subprocess.run(["mongodump", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("mongodump not found in PATH. Using alternative backup method.")
            return False
        
        # Run mongodump
        dump_path = output_path / "mongodump"
        dump_path.mkdir(exist_ok=True)
        
        cmd = [
            "mongodump",
            "--uri", connection_string,
            "--db", db_name,
            "--out", str(dump_path)
        ]
        
        process = subprocess.run(cmd, check=True, capture_output=True)
        
        if process.returncode == 0:
            logger.info(f"MongoDB backup created successfully using mongodump at {dump_path}")
            return True
        else:
            logger.error(f"mongodump failed: {process.stderr.decode()}")
            return False
    except Exception as e:
        logger.error(f"Error during mongodump: {e}")
        return False

def create_backup(backup_type='full', compress=True, connection_string=None, db_name=None):
    """
    Create a database backup.
    
    Args:
        backup_type (str, optional): Type of backup (full, users, transactions, etc.)
        compress (bool, optional): Whether to compress the backup
        connection_string (str, optional): MongoDB connection string
        db_name (str, optional): Database name
        
    Returns:
        tuple: (success, backup_path)
    """
    try:
        # Create backup directory
        backup_path = create_backup_directory()
        
        # Try mongodump first (preferred method)
        if connection_string is None:
            connection_string = current_app.config.get('MONGODB_URI')
        
        if db_name is None:
            db_name = current_app.config.get('MONGODB_DB_NAME')
        
        # Use the backup type to determine what to backup
        if backup_type == 'full':
            # Full database backup
            if backup_using_mongodump(connection_string, backup_path, db_name):
                logger.info("Backup created successfully using mongodump")
            else:
                # Fall back to PyMongo method
                logger.info("Falling back to PyMongo backup method")
                if not backup_using_pymongo(backup_path):
                    logger.error("Both backup methods failed")
                    return False, None
        elif backup_type == 'users':
            # Users-only backup
            if not backup_collection_using_pymongo(backup_path, 'users'):
                logger.error("Failed to backup users collection")
                return False, None
        elif backup_type == 'transactions':
            # Transactions-only backup
            if not backup_collection_using_pymongo(backup_path, 'transactions'):
                logger.error("Failed to backup transactions collection")
                return False, None
        elif backup_type == 'subscriptions':
            # Subscriptions-only backup
            if not backup_collection_using_pymongo(backup_path, 'subscriptionPlans'):
                logger.error("Failed to backup subscription plans collection")
                return False, None
        else:
            # Default to full backup
            if backup_using_mongodump(connection_string, backup_path, db_name):
                logger.info("Backup created successfully using mongodump")
            else:
                # Fall back to PyMongo method
                logger.info("Falling back to PyMongo backup method")
                if not backup_using_pymongo(backup_path):
                    logger.error("Both backup methods failed")
                    return False, None
        
        # Compress backup if requested
        if compress:
            tarball_path = compress_backup(backup_path)
        else:
            tarball_path = backup_path
        
        # Clean up old backups
        num_deleted = cleanup_old_backups()
        if num_deleted > 0:
            logger.info(f"Cleaned up {num_deleted} old backups")
        
        return True, tarball_path
    except BackupError as e:
        logger.error(f"Backup error: {e}")
        if e.original_error:
            logger.error(f"Original error: {e.original_error}")
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        return False, None

# Mock implementation of backup_collection_using_pymongo for collection-specific backups
def backup_collection_using_pymongo(output_path, collection_name):
    """
    Backup a specific collection using PyMongo.
    
    Args:
        output_path (Path): Directory to store the backup
        collection_name (str): Name of the collection to backup
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Connect to MongoDB
        db = MongoDB().get_db()
        if not db:
            MongoDB().connect()
            db = MongoDB().get_db()
            if not db:
                raise BackupError("Failed to connect to MongoDB")
        
        # Get the collection
        collection = db[collection_name]
        documents = list(collection.find())
        
        # Convert ObjectId to string
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            # Convert other potential ObjectIds
            for key, value in doc.items():
                if hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    doc[key] = str(value)
        
        # Create a directory for the backup files
        json_backup_path = output_path / "json_backup"
        json_backup_path.mkdir(exist_ok=True)
        
        # Write to file
        output_file = json_backup_path / f"{collection_name}.json"
        with open(output_file, "w") as f:
            json.dump(documents, f, indent=2, default=str)
        
        logger.info(f"Backed up collection {collection_name} with {len(documents)} documents")
        
        return True
    except Exception as e:
        logger.error(f"Error during {collection_name} backup: {e}")
        return False
    
def compress_backup(backup_path, delete_original=True):
    """
    Compress backup directory into a tarball.
    
    Args:
        backup_path (Path): Path to the backup directory
        delete_original (bool): Whether to delete the original directory after compression
        
    Returns:
        Path: Path to the compressed file
    """
    try:
        # Create tarball filename
        tarball_name = f"{backup_path.name}_backup.tar.gz"
        tarball_path = backup_path.parent / tarball_name
        
        # Create tarball
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        logger.info(f"Compressed backup created at {tarball_path}")
        
        # Delete original directory if requested
        if delete_original:
            shutil.rmtree(backup_path)
            logger.info(f"Deleted original backup directory: {backup_path}")
        
        return tarball_path
    except Exception as e:
        logger.error(f"Failed to compress backup: {e}")
        raise BackupError(f"Failed to compress backup: {e}", e)

def backup_using_pymongo(output_path):
    """
    Create a database backup using PyMongo.
    
    Args:
        output_path (Path): Directory to store the backup
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Connect to MongoDB
        db = MongoDB().get_db()
        if not db:
            MongoDB().connect()
            db = MongoDB().get_db()
            if not db:
                raise BackupError("Failed to connect to MongoDB")
        
        # Create a directory for the backup files
        json_backup_path = output_path / "json_backup"
        json_backup_path.mkdir(exist_ok=True)
        
        # Get list of all collections
        collections = db.list_collection_names()
        
        # Backup each collection
        for collection_name in collections:
            try:
                # Get the collection
                collection = db[collection_name]
                documents = list(collection.find())
                
                # Convert ObjectId to string for JSON serialization
                for doc in documents:
                    doc["_id"] = str(doc["_id"])
                    # Convert other potential ObjectIds
                    for key, value in doc.items():
                        if hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            doc[key] = str(value)
                
                # Write to file
                output_file = json_backup_path / f"{collection_name}.json"
                with open(output_file, "w") as f:
                    json.dump(documents, f, indent=2, default=str)
                
                logger.info(f"Backed up collection {collection_name} with {len(documents)} documents")
            except Exception as e:
                logger.error(f"Error backing up collection {collection_name}: {e}")
                # Continue with other collections even if one fails
        
        return True
    except Exception as e:
        logger.error(f"Error during PyMongo backup: {e}")
        return False
    
def cleanup_old_backups(backup_dir="backups", keep_last=5):
    """
    Remove old backups, keeping only the specified number of recent ones.
    
    Args:
        backup_dir (str): Base directory for backups
        keep_last (int): Number of recent backups to keep
        
    Returns:
        int: Number of backups deleted
    """
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            return 0
        
        # Get all backup files
        backup_files = list(backup_path.glob("*_backup.tar.gz"))
        backup_files.sort(key=lambda x: x.stat().st_mtime)
        
        # Determine files to delete
        files_to_delete = backup_files[:-keep_last] if len(backup_files) > keep_last else []
        
        # Delete old backups
        for file_path in files_to_delete:
            file_path.unlink()
            logger.info(f"Deleted old backup: {file_path}")
        
        return len(files_to_delete)
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")
        return 0