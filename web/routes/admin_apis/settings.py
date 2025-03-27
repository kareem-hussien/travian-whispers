"""
Settings management routes for Travian Whispers admin panel.
This module defines the settings management routes for the admin panel.
"""
import logging
from flask import render_template, request, redirect, url_for, flash, session

from web.utils.decorators import admin_required
from database.models.user import User
from database.models.settings import Settings

# Initialize logger
logger = logging.getLogger(__name__)

@admin_required
def index():
    """Admin settings page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get settings model
    settings_model = Settings()
    
    if request.method == 'POST':
        # Determine which settings form was submitted
        form_type = request.form.get('form_type', '')
        
        if form_type == 'general':
            # Process general settings form
            site_name = request.form.get('siteName')
            site_description = request.form.get('siteDescription')
            timezone = request.form.get('timezone')
            maintenance_mode = 'maintenanceMode' in request.form
            maintenance_message = request.form.get('maintenanceMessage')
            
            # Update settings in database
            settings_data = {
                'site_name': site_name,
                'site_description': site_description,
                'timezone': timezone,
                'maintenance_mode': maintenance_mode,
                'maintenance_message': maintenance_message
            }
            
            if settings_model.update_settings('general', settings_data):
                flash('General settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated general settings")
            else:
                flash('Failed to update general settings', 'danger')
                logger.error(f"Admin '{current_user['username']}' failed to update general settings")
                
        elif form_type == 'email':
            # Process email settings form
            smtp_server = request.form.get('smtpServer')
            smtp_port = request.form.get('smtpPort')
            smtp_username = request.form.get('smtpUsername')
            smtp_password = request.form.get('smtpPassword')
            sender_email = request.form.get('senderEmail')
            sender_name = request.form.get('senderName')
            
            # Update settings in database
            settings_data = {
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'smtp_username': smtp_username,
                'sender_email': sender_email,
                'sender_name': sender_name
            }
            
            # Only update password if provided
            if smtp_password and not smtp_password.startswith('••••'):
                settings_data['smtp_password'] = smtp_password
            
            if settings_model.update_settings('email', settings_data):
                flash('Email settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated email settings")
            else:
                flash('Failed to update email settings', 'danger')
                logger.error(f"Admin '{current_user['username']}' failed to update email settings")
                
        elif form_type == 'payment':
            # Process payment settings form
            paypal_mode = request.form.get('paypalMode')
            paypal_client_id = request.form.get('paypalClientId')
            paypal_secret = request.form.get('paypalSecret')
            paypal_enabled = 'paypalEnabled' in request.form
            
            # Update settings in database
            settings_data = {
                'paypal_mode': paypal_mode,
                'paypal_client_id': paypal_client_id,
                'paypal_enabled': paypal_enabled
            }
            
            # Only update secret if provided
            if paypal_secret and not paypal_secret.startswith('••••'):
                settings_data['paypal_secret'] = paypal_secret
            
            if settings_model.update_settings('payment', settings_data):
                flash('Payment settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated payment settings")
            else:
                flash('Failed to update payment settings', 'danger')
                logger.error(f"Admin '{current_user['username']}' failed to update payment settings")
                
        elif form_type == 'security':
            # Process security settings form
            email_verification = 'emailVerification' in request.form
            session_timeout = request.form.get('sessionTimeout')
            max_login_attempts = request.form.get('maxLoginAttempts')
            account_lock_duration = request.form.get('accountLockDuration')
            password_policy = request.form.get('passwordPolicy')
            
            # Update settings in database
            settings_data = {
                'email_verification': email_verification,
                'session_timeout': int(session_timeout),
                'max_login_attempts': int(max_login_attempts),
                'account_lock_duration': int(account_lock_duration),
                'password_policy': password_policy
            }
            
            if settings_model.update_settings('security', settings_data):
                flash('Security settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated security settings")
            else:
                flash('Failed to update security settings', 'danger')
                logger.error(f"Admin '{current_user['username']}' failed to update security settings")
                
        elif form_type == 'backup':
            # Process backup settings form
            auto_backup = 'autoBackup' in request.form
            backup_frequency = request.form.get('backupFrequency')
            retention_period = request.form.get('retentionPeriod')
            
            # Update settings in database
            settings_data = {
                'auto_backup': auto_backup,
                'backup_frequency': backup_frequency,
                'retention_period': int(retention_period)
            }
            
            if settings_model.update_settings('backup', settings_data):
                flash('Backup settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated backup settings")
            else:
                flash('Failed to update backup settings', 'danger')
                logger.error(f"Admin '{current_user['username']}' failed to update backup settings")
        
        return redirect(url_for('admin.settings', _anchor=form_type))
    
    # Get settings from database
    settings = settings_model.get_all_settings()
    
    # Render settings template
    return render_template(
        'admin/settings.html', 
        settings=settings, 
        current_user=current_user,
        title='System Settings'
    )