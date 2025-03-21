"""
Models package for Travian Whispers web application.
This module provides helper functions for working with database models.
"""
import logging
from bson import ObjectId
from flask import current_app
from database.mongodb import MongoDB

# Initialize logger
logger = logging.getLogger(__name__)


def get_db():
    """
    Get the database connection from the Flask application context.
    
    Returns:
        pymongo.database.Database: Database instance or None if not connected
    """
    if hasattr(current_app, 'db'):
        return current_app.db.get_db()
    
    # Fall back to creating a new connection if not in app context
    db = MongoDB().get_db()
    
    if db is None:
        logger.warning("Database not connected. Call connect() first.")
    
    return db


def get_collection(collection_name):
    """
    Get a collection by name.
    
    Args:
        collection_name (str): Name of the collection
        
    Returns:
        pymongo.collection.Collection: Collection instance or None if not found
    """
    db = get_db()
    
    if db is None:
        return None
    
    return db[collection_name]


def is_valid_id(id_string):
    """
    Check if a string is a valid MongoDB ObjectId.
    
    Args:
        id_string (str): String to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ObjectId(id_string)
        return True
    except (TypeError, ValueError):
        return False


def dict_to_model(data, model_class):
    """
    Convert a dictionary to a model instance.
    
    Args:
        data (dict): Dictionary to convert
        model_class (class): Model class to instantiate
        
    Returns:
        object: Model instance
    """
    return model_class(**data)


def model_to_dict(model, exclude=None):
    """
    Convert a model instance to a dictionary.
    
    Args:
        model (object): Model instance to convert
        exclude (list, optional): Fields to exclude
        
    Returns:
        dict: Dictionary representation of model
    """
    exclude = exclude or []
    return {k: v for k, v in model.__dict__.items() if not k.startswith('_') and k not in exclude}


def paginate_query(collection, query, page=1, per_page=20, sort_by=None, sort_direction=-1):
    """
    Paginate a database query.
    
    Args:
        collection (pymongo.collection.Collection): Collection to query
        query (dict): Query filter
        page (int, optional): Page number
        per_page (int, optional): Items per page
        sort_by (str, optional): Field to sort by
        sort_direction (int, optional): Sort direction (1 for ascending, -1 for descending)
        
    Returns:
        tuple: (items, total, page, per_page, pages)
    """
    # Ensure positive values
    page = max(1, page)
    per_page = max(1, per_page)
    
    # Calculate skip and limit values
    skip = (page - 1) * per_page
    
    # Get total count
    total = collection.count_documents(query)
    
    # Get items for current page
    cursor = collection.find(query).skip(skip).limit(per_page)
    
    # Apply sorting if specified
    if sort_by:
        cursor = cursor.sort(sort_by, sort_direction)
    
    # Convert cursor to list
    items = list(cursor)
    
    # Calculate total pages
    pages = (total + per_page - 1) // per_page  # Ceiling division
    
    return items, total, page, per_page, pages