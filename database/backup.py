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

def encrypt_backup(backup_path, output_path=None):
    """
    Encrypt a backup file.
    
    Args:
        backup_path (Path): Path to the backup file
        output_path (Path, optional): Path to save the encrypted file
        
    Returns:
        Path: Path to the encrypted file
    """
    if not output_path:
        output_path = backup_path.with_suffix('.enc')
    
    try:
        with open(backup_path, 'rb') as f:
            data = f.read()
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        logger.info(f"Backup encrypted and saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to encrypt backup: {e}")
        raise BackupError(f"Failed to encrypt backup: {e}", e)
    
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

def backup_using_pymongo(output_path):
    """
    Create a backup using PyMongo (alternative method).
    
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
        
        # Get all collections
        collections = db.list_collection_names()
        logger.info(f"Found {len(collections)} collections to backup")
        
        # Create a directory for the backup files
        json_backup_path = output_path / "json_backup"
        json_backup_path.mkdir(exist_ok=True)
        
        # Backup each collection
        for collection_name in collections:
            collection = db[collection_name]
            documents = list(collection.find())
            
            # Convert ObjectId to string
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
        
        logger.info(f"MongoDB backup created successfully using PyMongo at {json_backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error during PyMongo backup: {e}")
        raise BackupError(f"Failed to create backup using PyMongo: {e}", e)

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

def create_backup(connection)