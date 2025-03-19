"""
Backup Record model for Travian Whispers application.
This module provides the BackupRecord model for tracking database backups.
"""
import logging
from datetime import datetime
import os
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class BackupRecord:
    """BackupRecord model for tracking database backups."""
    
    def __init__(self):
        """Initialize BackupRecord model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["backupRecords"]
    
    def add_backup_record(self, filename, backup_type='full', file_size=0, success=True, details=None):
        """
        Add a new backup record.
        
        Args:
            filename (str): Backup filename
            backup_type (str, optional): Type of backup (full, users, transactions, etc.)
            file_size (int, optional): Size of backup file in bytes
            success (bool, optional): Whether backup was successful
            details (str, optional): Additional details about the backup
            
        Returns:
            dict: New backup record or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            # Format file size
            formatted_size = self._format_file_size(file_size)
            
            record_data = {
                "filename": filename,
                "type": backup_type,
                "size": formatted_size,
                "raw_size": file_size,
                "success": success,
                "details": details,
                "created_at": datetime.utcnow()
            }
            
            result = self.collection.insert_one(record_data)
            
            if result.inserted_id:
                record_data['_id'] = result.inserted_id
                return record_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to add backup record: {e}")
            return None
    
    def _format_file_size(self, size_bytes):
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes (int): Size in bytes
            
        Returns:
            str: Formatted size
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def get_backup_record(self, record_id):
        """
        Get a backup record by ID.
        
        Args:
            record_id (str): Record ID
            
        Returns:
            dict: Backup record or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            record_oid = ObjectId(record_id)
            record = self.collection.find_one({"_id": record_oid})
            return record
        except Exception as e:
            logger.error(f"Failed to get backup record: {e}")
            return None
    
    def get_backup_by_filename(self, filename):
        """
        Get a backup record by filename.
        
        Args:
            filename (str): Backup filename
            
        Returns:
            dict: Backup record or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            record = self.collection.find_one({"filename": filename})
            return record
        except Exception as e:
            logger.error(f"Failed to get backup record: {e}")
            return None
    
    def list_backups(self, limit=10, backup_type=None):
        """
        List backup records.
        
        Args:
            limit (int, optional): Maximum number of records to return
            backup_type (str, optional): Filter by backup type
            
        Returns:
            list: List of backup records
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            query = {}
            
            if backup_type:
                query["type"] = backup_type
            
            records = self.collection.find(query).sort("created_at", -1).limit(limit)
            return list(records)
        except Exception as e:
            logger.error(f"Failed to list backup records: {e}")
            return []
    
    def delete_record(self, record_id):
        """
        Delete a backup record.
        
        Args:
            record_id (str): Record ID
            
        Returns:
            bool: True if record was deleted, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            record_oid = ObjectId(record_id)
            
            # Get record to delete associated file
            record = self.collection.find_one({"_id": record_oid})
            
            if record and "filename" in record:
                # Delete backup file if it exists
                backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
                backup_path = os.path.join(backup_dir, record["filename"])
                
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    logger.info(f"Deleted backup file: {backup_path}")
            
            # Delete record
            result = self.collection.delete_one({"_id": record_oid})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete backup record: {e}")
            return False
    
    def delete_old_backups(self, days_to_keep, backup_type=None):
        """
        Delete backup records and files older than the specified number of days.
        
        Args:
            days_to_keep (int): Number of days to keep backups
            backup_type (str, optional): Filter by backup type
            
        Returns:
            int: Number of deleted backups
        """
        if self.collection is None:
            logger.error("Database not connected")
            return 0
        
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            query = {"created_at": {"$lt": cutoff_date}}
            
            if backup_type:
                query["type"] = backup_type
            
            # Get records to delete associated files
            records = self.collection.find(query)
            
            count = 0
            for record in records:
                if "filename" in record:
                    # Delete backup file if it exists
                    backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
                    backup_path = os.path.join(backup_dir, record["filename"])
                    
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        logger.info(f"Deleted old backup file: {backup_path}")
                
                count += 1
            
            # Delete records
            result = self.collection.delete_many(query)
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old backup records: {e}")
            return 0
            
    def update_backup_status(self, record_id, success, details=None):
        """
        Update backup status.
        
        Args:
            record_id (str): Record ID
            success (bool): Whether backup was successful
            details (str, optional): Additional details about the backup
            
        Returns:
            bool: True if status was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            record_oid = ObjectId(record_id)
            
            update_data = {"success": success}
            
            if details:
                update_data["details"] = details
            
            result = self.collection.update_one(
                {"_id": record_oid},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update backup status: {e}")
            return False
