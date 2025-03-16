"""
Custom JSON encoder for Travian Whispers web application.
This module provides a custom JSON encoder for Flask.
"""
import json
from bson import ObjectId
from datetime import datetime
from flask.json import JSONEncoder


class TravianJSONEncoder(JSONEncoder):
    """Custom JSON encoder that handles ObjectId and datetime objects."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(TravianJSONEncoder, self).default(obj)