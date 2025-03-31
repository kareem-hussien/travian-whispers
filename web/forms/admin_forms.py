"""
Admin forms for Travian Whispers web application.
This module defines forms for admin panel routes.
"""
import logging
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, SelectField, 
    IntegerField, FloatField, BooleanField, TextAreaField,
    MultipleFileField, DateTimeField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, 
    Optional, NumberRange, ValidationError
)

from web.forms import validate_username, validate_password_strength

# Initialize logger
logger = logging.getLogger(__name__)


class UserCreateForm(FlaskForm):
    """User creation form for admin panel."""
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
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ], default='user')
    verified = BooleanField('Verified Email', default=True)


class UserEditForm(FlaskForm):
    """User edit form for admin panel."""
    user_id = HiddenField('User ID')
    email = EmailField('Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        validate_password_strength
    ])
    # Add subscription fields
    subscription_status = SelectField('Subscription Status', choices=[
        ('inactive', 'Inactive'),
        ('active', 'Active')
    ])
    subscription_plan = SelectField('Subscription Plan', choices=[], validators=[Optional()])
    billing_period = SelectField('Billing Period', choices=[
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], default='monthly')


class PlanCreateForm(FlaskForm):
    """Subscription plan creation form for admin panel."""
    name = StringField('Plan Name', validators=[
        DataRequired(message='Plan name is required'),
        Length(min=3, max=50, message='Plan name must be 3-50 characters long')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required'),
        Length(min=10, max=500, message='Description must be 10-500 characters long')
    ])
    monthly_price = FloatField('Monthly Price ($)', validators=[
        DataRequired(message='Monthly price is required'),
        NumberRange(min=0, message='Price must be a positive number')
    ])
    yearly_price = FloatField('Yearly Price ($)', validators=[
        DataRequired(message='Yearly price is required'),
        NumberRange(min=0, message='Price must be a positive number')
    ])
    feature_auto_farm = BooleanField('Auto-Farm Feature', default=False)
    feature_trainer = BooleanField('Troop Training', default=False)
    feature_notification = BooleanField('Notifications', default=True)
    feature_advanced = BooleanField('Advanced Features', default=False)
    max_villages = IntegerField('Maximum Villages', validators=[
        DataRequired(message='Maximum villages is required'),
        NumberRange(min=1, message='Maximum villages must be at least 1')
    ], default=2)
    max_tasks = IntegerField('Maximum Concurrent Tasks', validators=[
        DataRequired(message='Maximum tasks is required'),
        NumberRange(min=1, message='Maximum tasks must be at least 1')
    ], default=1)


class PlanEditForm(FlaskForm):
    """Subscription plan edit form for admin panel."""
    plan_id = HiddenField('Plan ID')
    name = StringField('Plan Name', validators=[
        DataRequired(message='Plan name is required'),
        Length(min=3, max=50, message='Plan name must be 3-50 characters long')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required'),
        Length(min=10, max=500, message='Description must be 10-500 characters long')
    ])
    monthly_price = FloatField('Monthly Price ($)', validators=[
        DataRequired(message='Monthly price is required'),
        NumberRange(min=0, message='Price must be a positive number')
    ])
    yearly_price = FloatField('Yearly Price ($)', validators=[
        DataRequired(message='Yearly price is required'),
        NumberRange(min=0, message='Price must be a positive number')
    ])
    feature_auto_farm = BooleanField('Auto-Farm Feature')
    feature_trainer = BooleanField('Troop Training')
    feature_notification = BooleanField('Notifications')
    feature_advanced = BooleanField('Advanced Features')
    max_villages = IntegerField('Maximum Villages', validators=[
        DataRequired(message='Maximum villages is required'),
        NumberRange(min=1, message='Maximum villages must be at least 1')
    ])
    max_tasks = IntegerField('Maximum Concurrent Tasks', validators=[
        DataRequired(message='Maximum tasks is required'),
        NumberRange(min=1, message='Maximum tasks must be at least 1')
    ])


class TransactionUpdateForm(FlaskForm):
    """Transaction status update form for admin panel."""
    transaction_id = HiddenField('Transaction ID')
    status = SelectField('Status', choices=[
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ])


class BackupForm(FlaskForm):
    """Database backup form for admin panel."""
    backup_type = SelectField('Backup Type', choices=[
        ('full', 'Full Backup'),
        ('users', 'Users Only'),
        ('transactions', 'Transactions Only'),
        ('subscriptions', 'Subscriptions Only')
    ], default='full')
    compress_backup = BooleanField('Compress Backup', default=True)


class MaintenanceForm(FlaskForm):
    """Maintenance mode form for admin panel."""
    enabled = BooleanField('Enable Maintenance Mode')
    message = TextAreaField('Maintenance Message', validators=[
        DataRequired(message='Maintenance message is required'),
        Length(min=10, max=500, message='Message must be 10-500 characters long')
    ], default='We are currently performing scheduled maintenance. Please check back later.')
    duration = SelectField('Expected Duration', choices=[
        ('30min', '30 minutes'),
        ('1hour', '1 hour'),
        ('2hours', '2 hours'),
        ('4hours', '4 hours'),
        ('indefinite', 'Indefinite')
    ], default='indefinite')


class GenerateReportForm(FlaskForm):
    """Report generation form for admin panel."""
    report_type = SelectField('Report Type', choices=[
        ('users', 'User Report'),
        ('transactions', 'Transaction Report'),
        ('subscriptions', 'Subscription Report'),
        ('system', 'System Performance Report')
    ])
    date_range = SelectField('Date Range', choices=[
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('last7days', 'Last 7 Days'),
        ('last30days', 'Last 30 Days'),
        ('thisMonth', 'This Month'),
        ('lastMonth', 'Last Month'),
        ('custom', 'Custom Range')
    ], default='last7days')
    start_date = DateTimeField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateTimeField('End Date', format='%Y-%m-%d', validators=[Optional()])
    report_format = SelectField('Format', choices=[
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel')
    ], default='pdf')


class EmailUsersForm(FlaskForm):
    """Email users form for admin panel."""
    recipients = SelectField('Recipients', choices=[
        ('all', 'All Users'),
        ('active', 'Users with Active Subscriptions'),
        ('expired', 'Users with Expired Subscriptions'),
        ('unverified', 'Unverified Users'),
        ('selected', 'Selected Users')
    ], default='all')
    subject = StringField('Subject', validators=[
        DataRequired(message='Subject is required'),
        Length(min=3, max=100, message='Subject must be 3-100 characters long')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(message='Message is required'),
        Length(min=10, message='Message must be at least 10 characters long')
    ])
    selected_users = HiddenField('Selected Users')


class SystemSettingsForm(FlaskForm):
    """System settings form for admin panel."""
    site_name = StringField('Site Name', validators=[
        DataRequired(message='Site name is required'),
        Length(min=3, max=50, message='Site name must be 3-50 characters long')
    ], default='Travian Whispers')
    site_description = TextAreaField('Site Description', validators=[
        DataRequired(message='Site description is required'),
        Length(min=10, max=200, message='Site description must be 10-200 characters long')
    ], default='Advanced Travian Automation Suite')
    timezone = SelectField('Default Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'America/New_York'),
        ('Europe/London', 'Europe/London'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
        ('Australia/Sydney', 'Australia/Sydney')
    ], default='UTC')
    maintenance_mode = BooleanField('Enable Maintenance Mode')
    maintenance_message = TextAreaField('Maintenance Message', validators=[
        Length(min=10, max=500, message='Message must be 10-500 characters long')
    ], default='We are currently performing scheduled maintenance. Please check back later.')
    
    