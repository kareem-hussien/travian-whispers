"""
JSON utilities for Travian Whispers web application.
This module provides utility functions for JSON serialization.
"""
import logging
import json
from bson import ObjectId
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

def to_json(obj):
    """
    Convert an object to a JSON-compatible format.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-compatible object
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat() if obj else None
    # Let the default encoder handle it
    raise TypeError(f"Type {type(obj)} not serializable")

def dumps(obj, **kwargs):
    """
    Serialize an object to a JSON string.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps()
        
    Returns:
        str: JSON string
    """
    return json.dumps(obj, default=to_json, **kwargs)

def loads(s, **kwargs):
    """
    Deserialize a JSON string to a Python object.
    
    Args:
        s: JSON string
        **kwargs: Additional arguments for json.loads()
        
    Returns:
        Deserialized Python object
    """
    return json.loads(s, **kwargs)

def jsonify_custom(obj):
    """
    Create a Flask JSON response with custom serialization.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON response object
    """
    from flask import Response
    
    # First serialize the object to a JSON string
    json_str = dumps(obj)
    
    # Create a Response object with the correct content type
    response = Response(json_str, mimetype='application/json')
    
    return response
