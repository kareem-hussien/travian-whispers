"""
Custom JSON encoder for Travian Whispers web application.
This module provides a custom JSON encoder for Flask.
"""
import json
from bson import ObjectId
from datetime import datetime

class TravianJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles ObjectId and datetime objects."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(TravianJSONEncoder, self).default(obj)

def setup_json_encoder(app):
    """
    Configure the Flask app to use the custom JSON encoder.
    This approach works with all Flask versions.
    
    Args:
        app: Flask application instance
    """
    # Method 1: For Flask 2.x+, use app.json.encoder
    if hasattr(app, 'json') and hasattr(app.json, 'encoder'):
        app.json.encoder = TravianJSONEncoder
        return
        
    # Method 2: For older Flask, use app.json_encoder
    app.json_encoder = TravianJSONEncoder