"""
Forms package for Travian Whispers web application.
This module initializes the forms package and provides common form utilities.
"""
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from wtforms.widgets import TextArea

# Initialize logger
logger = logging.getLogger(__name__)

# Common form validators and utilities can be defined here
def validate_username(form, field):
    """Validate username format (alphanumeric with underscores, starts with a letter)."""
    import re
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,19}$', field.data):
        raise ValidationError('Username must start with a letter and contain only letters, numbers, and underscores (3-20 characters).')

def validate_password_strength(form, field):
    """Validate password strength."""
    import re
    
    if len(field.data) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    
    if not re.search(r'[A-Z]', field.data):
        raise ValidationError('Password must contain at least one uppercase letter.')
    
    if not re.search(r'[a-z]', field.data):
        raise ValidationError('Password must contain at least one lowercase letter.')
    
    if not re.search(r'\d', field.data):
        raise ValidationError('Password must contain at least one digit.')