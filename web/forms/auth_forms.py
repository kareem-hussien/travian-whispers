"""
Authentication forms for Travian Whispers web application.
This module defines forms for authentication-related routes.
"""
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, EmailField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError

from web.forms import validate_username, validate_password_strength

# Initialize logger
logger = logging.getLogger(__name__)


class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username or Email', validators=[
        DataRequired(message='Username or email is required')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember = BooleanField('Remember me')


class RegistrationForm(FlaskForm):
    """Registration form."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be 3-20 characters long'),
        validate_username
    ])
    email = EmailField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    terms = BooleanField('I agree to the Terms & Conditions and Privacy Policy', validators=[
        DataRequired(message='You must accept the Terms and Conditions')
    ])


class ForgotPasswordForm(FlaskForm):
    """Forgot password form."""
    email = EmailField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])


class ResetPasswordForm(FlaskForm):
    """Reset password form."""
    token = HiddenField('Token')
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])


class ResendVerificationForm(FlaskForm):
    """Resend verification email form."""
    email = EmailField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])


class ChangePasswordForm(FlaskForm):
    """Change password form."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])