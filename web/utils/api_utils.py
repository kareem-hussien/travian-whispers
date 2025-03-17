"""
API utilities for Travian Whispers web application.
This module provides utility functions for API endpoints.
"""
import logging
import json
from flask import Response, make_response
from bson import ObjectId
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

def custom_json_encoder(obj):
    """
    Custom JSON encoder for MongoDB ObjectId and datetime objects.
    
    Args:
        obj: Object to encode
        
    Returns:
        JSON serializable object
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat() if obj else None
    raise TypeError(f"Type {type(obj)} not serializable")

def jsonify(data, status=200):
    """
    Create a JSON response with the correct content type.
    
    Args:
        data: Data to serialize
        status: HTTP status code
        
    Returns:
        Flask response object
    """
    # First serialize the data to a JSON string
    try:
        json_str = json.dumps(data, default=custom_json_encoder)
    except TypeError as e:
        logger.error(f"JSON serialization error: {e}")
        json_str = json.dumps({
            "success": False,
            "message": "Data serialization error"
        })
        status = 500
    
    # Create a response with the correct content type
    response = make_response(json_str, status)
    response.headers['Content-Type'] = 'application/json'
    
    return response

def success_response(data=None, message=None):
    """
    Create a success JSON response.
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        JSON response object
    """
    response_data = {"success": True}
    
    if message:
        response_data["message"] = message
    
    if data:
        response_data["data"] = data
    
    return jsonify(response_data)

def error_response(message, status=400, errors=None):
    """
    Create an error JSON response.
    
    Args:
        message: Error message
        status: HTTP status code
        errors: Additional error details
        
    Returns:
        JSON response object
    """
    response_data = {
        "success": False,
        "message": message
    }
    
    if errors:
        response_data["errors"] = errors
    
    return jsonify(response_data, status)
