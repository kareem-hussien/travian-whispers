"""
FAQ model for Travian Whispers application.
This module provides the FAQ model for managing frequently asked questions.
"""
import logging
from datetime import datetime
from bson import ObjectId
from flask import current_app

# Initialize logger
logger = logging.getLogger(__name__)


class FAQ:
    """FAQ model for managing frequently asked questions."""
    
    def __init__(self):
        """Initialize FAQ model."""
        self.db = None
        self.collection = None
        
        if hasattr(current_app, 'db'):
            self.db = current_app.db.get_db()
            
        if self.db is not None:
            self.collection = self.db["faq"]
    
    def add_faq_entry(self, question, answer, category='general', order=0):
        """
        Add a new FAQ entry.
        
        Args:
            question (str): Question text
            answer (str): Answer text
            category (str, optional): FAQ category
            order (int, optional): Display order
            
        Returns:
            dict: New FAQ entry or None if failed
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            faq_data = {
                "question": question,
                "answer": answer,
                "category": category,
                "order": order,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            result = self.collection.insert_one(faq_data)
            
            if result.inserted_id:
                faq_data['_id'] = result.inserted_id
                return faq_data
            
            return None
        except Exception as e:
            logger.error(f"Failed to add FAQ entry: {e}")
            return None
    
    def get_faq_entry(self, entry_id):
        """
        Get an FAQ entry by ID.
        
        Args:
            entry_id (str): Entry ID
            
        Returns:
            dict: FAQ entry or None if not found
        """
        if self.collection is None:
            logger.error("Database not connected")
            return None
        
        try:
            entry_oid = ObjectId(entry_id)
            entry = self.collection.find_one({"_id": entry_oid})
            return entry
        except Exception as e:
            logger.error(f"Failed to get FAQ entry: {e}")
            return None
    
    def update_faq_entry(self, entry_id, update_data):
        """
        Update an FAQ entry.
        
        Args:
            entry_id (str): Entry ID
            update_data (dict): Updated data
            
        Returns:
            bool: True if entry was updated, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            entry_oid = ObjectId(entry_id)
            
            # Add updated timestamp
            update_data["updatedAt"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": entry_oid},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update FAQ entry: {e}")
            return False
    
    def delete_faq_entry(self, entry_id):
        """
        Delete an FAQ entry.
        
        Args:
            entry_id (str): Entry ID
            
        Returns:
            bool: True if entry was deleted, False otherwise
        """
        if self.collection is None:
            logger.error("Database not connected")
            return False
        
        try:
            entry_oid = ObjectId(entry_id)
            
            result = self.collection.delete_one({"_id": entry_oid})
            
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete FAQ entry: {e}")
            return False
    
    def list_faq_entries(self, category=None):
        """
        List FAQ entries, optionally filtered by category.
        
        Args:
            category (str, optional): Category to filter by
            
        Returns:
            list: List of FAQ entries
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            query = {}
            
            if category:
                query["category"] = category
            
            entries = self.collection.find(query).sort("order", 1)
            return list(entries)
        except Exception as e:
            logger.error(f"Failed to list FAQ entries: {e}")
            return []
    
    def list_categories(self):
        """
        List all FAQ categories.
        
        Returns:
            list: List of unique categories
        """
        if self.collection is None:
            logger.error("Database not connected")
            return []
        
        try:
            categories = self.collection.distinct("category")
            return list(categories)
        except Exception as e:
            logger.error(f"Failed to list FAQ categories: {e}")
            return []
