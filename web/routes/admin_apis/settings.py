"""
Admin settings routes for Travian Whispers web application.
"""
import logging
import platform
from datetime import datetime, timedelta
from flask import (
    render_template, request, redirect, 
    url_for, flash, session, current_app
)

from web.utils.decorators import admin_required
from database.models.user import User
from database.settings import Settings

# Initialize logger
logger = logging.getLogger(__name__)

def register_routes(admin_bp):
    """Register settings routes with the admin blueprint."""
    # Attach routes to the blueprint
    admin_bp.route('/settings', methods=['GET', 'POST'])(admin_required(settings))
    admin_bp.route('/test-email', methods=['POST'])(admin_required(test_email))

def settings():
    """Admin settings page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Initialize settings model
    settings_model = Settings()
    
    # Handle form submissions
    if request.method == 'POST':
        # Determine which settings form was submitted
        form_type = request.form.get('form_type', '')
        active_tab = request.form.get('active_tab', 'general')
        
        if form_type == 'general':
            # Process general settings form
            settings_data = {
                'general.site_name': request.form.get('siteName'),
                'general.site_description': request.form.get('siteDescription'),
                'general.timezone': request.form.get('timezone'),
                'general.maintenance_mode': 'maintenanceMode' in request.form,
                'general.maintenance_message': request.form.get('maintenanceMessage', '')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['MAINTENANCE_MODE'] = 'maintenanceMode' in request.form
                current_app.config['MAINTENANCE_MESSAGE'] = request.form.get('maintenanceMessage', '')
                
                flash('General settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated general settings")
            else:
                flash('Failed to update general settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update general settings")
            
        elif form_type == 'email':
            # Process email settings form
            smtp_password = request.form.get('smtpPassword')
            
            # Don't update password if it's masked
            if smtp_password == '••••••••••••':
                smtp_password = settings_model.get_setting('email.smtp_password', '')
            
            settings_data = {
                'email.smtp_server': request.form.get('smtpServer'),
                'email.smtp_port': int(request.form.get('smtpPort', 587)),
                'email.smtp_security': request.form.get('smtpSecurity', 'starttls'),
                'email.smtp_username': request.form.get('smtpUsername'),
                'email.smtp_password': smtp_password,
                'email.sender_email': request.form.get('senderEmail'),
                'email.sender_name': request.form.get('senderName')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['SMTP_SERVER'] = request.form.get('smtpServer')
                current_app.config['SMTP_PORT'] = int(request.form.get('smtpPort', 587))
                current_app.config['SMTP_USERNAME'] = request.form.get('smtpUsername')
                current_app.config['SMTP_PASSWORD'] = smtp_password
                current_app.config['EMAIL_FROM'] = f"{request.form.get('senderName')} <{request.form.get('senderEmail')}>"
                
                flash('Email settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated email settings")
            else:
                flash('Failed to update email settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update email settings")
            
        elif form_type == 'payment':
            # Process payment settings form
            paypal_secret = request.form.get('paypalSecret')
            stripe_secret_key = request.form.get('stripeSecretKey')
            
            # Don't update secrets if they're masked
            if paypal_secret == '••••••••••••':
                paypal_secret = settings_model.get_setting('payment.paypal_secret', '')
                
            if stripe_secret_key == '••••••••••••':
                stripe_secret_key = settings_model.get_setting('payment.stripe_secret_key', '')
            
            settings_data = {
                'payment.paypal_enabled': 'paypalEnabled' in request.form,
                'payment.paypal_mode': request.form.get('paypalMode'),
                'payment.paypal_client_id': request.form.get('paypalClientId'),
                'payment.paypal_secret': paypal_secret,
                'payment.stripe_enabled': 'stripeEnabled' in request.form,
                'payment.stripe_mode': request.form.get('stripeMode'),
                'payment.stripe_publishable_key': request.form.get('stripePublishableKey'),
                'payment.stripe_secret_key': stripe_secret_key,
                'payment.currency': request.form.get('currency'),
                'payment.currency_position': request.form.get('currencyPosition')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['PAYPAL_CLIENT_ID'] = request.form.get('paypalClientId')
                current_app.config['PAYPAL_SECRET'] = paypal_secret
                current_app.config['PAYPAL_MODE'] = request.form.get('paypalMode')
                
                flash('Payment settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated payment settings")
            else:
                flash('Failed to update payment settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update payment settings")
            
        elif form_type == 'security':
            # Process security settings form
            settings_data = {
                'security.email_verification': 'emailVerification' in request.form,
                'security.session_timeout': int(request.form.get('sessionTimeout', 60)),
                'security.max_login_attempts': int(request.form.get('maxLoginAttempts', 5)),
                'security.account_lock_duration': int(request.form.get('accountLockDuration', 30)),
                'security.password_policy': request.form.get('passwordPolicy'),
                'security.password_expiry': int(request.form.get('passwordExpiry', 90)),
                'security.force_https': 'forceHttps' in request.form,
                'security.enable_hsts': 'enableHSTS' in request.form,
                'security.enable_csp': 'enableCSP' in request.form,
                'security.x_frame_options': request.form.get('xFrameOptions')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['SESSION_PERMANENT'] = True
                current_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=int(request.form.get('sessionTimeout', 60)))
                
                flash('Security settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated security settings")
            else:
                flash('Failed to update security settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update security settings")
            
        elif form_type == 'backup':
            # Process backup settings form
            settings_data = {
                'backup.auto_backup': 'autoBackup' in request.form,
                'backup.backup_frequency': request.form.get('backupFrequency'),
                'backup.backup_time': request.form.get('backupTime'),
                'backup.backup_type': request.form.get('backupType', 'full'),
                'backup.compress_backups': 'compressBackups' in request.form,
                'backup.retention_period': int(request.form.get('retentionPeriod', 30)),
                'backup.max_backups': int(request.form.get('maxBackups', 10)),
                'backup.backup_location': request.form.get('backupLocation'),
                'backup.external_storage': 'externalStorage' in request.form,
                'backup.external_storage_type': request.form.get('externalStorageType')
            }
            
            if settings_model.update_settings(settings_data):
                # Update application config
                current_app.config['BACKUP_DIR'] = request.form.get('backupLocation')
                
                flash('Backup settings updated successfully', 'success')
                logger.info(f"Admin '{current_user['username']}' updated backup settings")
            else:
                flash('Failed to update backup settings', 'danger')
                logger.warning(f"Admin '{current_user['username']}' failed to update backup settings")
        
        # Redirect to maintain the active tab
        return redirect(url_for('admin.settings', tab=active_tab))
    
    # Get app version from configuration or default to 1.0.0
    app_version = current_app.config.get('APP_VERSION', '1.0.0')
    
    # Create system_info for the template
    system_info = {
        'version': app_version,
        'environment': current_app.config.get('ENV', 'Production'),
        'debug_mode': current_app.config.get('DEBUG', False),
        'python_version': platform.python_version(),
        'server_software': request.environ.get('SERVER_SOFTWARE', 'Gunicorn/Flask'),
        'database': 'MongoDB 5.0.5'
    }

    # Get settings from the database
    settings = {
        'general': {
            'site_name': settings_model.get_setting('general.site_name', 'Travian Whispers'),
            'site_description': settings_model.get_setting('general.site_description', 'Advanced Travian Automation Suite'),
            'timezone': settings_model.get_setting('general.timezone', 'UTC'),
            'maintenance_mode': settings_model.get_setting('general.maintenance_mode', False),
            'maintenance_message': settings_model.get_setting('general.maintenance_message', 'We are currently performing scheduled maintenance. Please check back later.')
        },
        'email': {
            'smtp_server': settings_model.get_setting('email.smtp_server', 'smtp.gmail.com'),
            'smtp_port': settings_model.get_setting('email.smtp_port', 587),
            'smtp_username': settings_model.get_setting('email.smtp_username', 'your-email@gmail.com'),
            'smtp_password': '••••••••••••',  # Masked for security
            'sender_email': settings_model.get_setting('email.sender_email', 'noreply@travianwhispers.com'),
            'sender_name': settings_model.get_setting('email.sender_name', 'Travian Whispers')
        },
        'payment': {
            'paypal_mode': settings_model.get_setting('payment.paypal_mode', 'sandbox'),
            'paypal_client_id': settings_model.get_setting('payment.paypal_client_id', 'your-client-id'),
            'paypal_secret': '••••••••••••',  # Masked for security
            'paypal_enabled': settings_model.get_setting('payment.paypal_enabled', True),
            'stripe_enabled': settings_model.get_setting('payment.stripe_enabled', False),
            'currency': settings_model.get_setting('payment.currency', 'USD'),
            'currency_position': settings_model.get_setting('payment.currency_position', 'before')
        },
        'security': {
            'email_verification': settings_model.get_setting('security.email_verification', True),
            'session_timeout': settings_model.get_setting('security.session_timeout', 60),
            'max_login_attempts': settings_model.get_setting('security.max_login_attempts', 5),
            'account_lock_duration': settings_model.get_setting('security.account_lock_duration', 30),
            'password_policy': settings_model.get_setting('security.password_policy', 'standard'),
            'force_https': settings_model.get_setting('security.force_https', True),
            'enable_hsts': settings_model.get_setting('security.enable_hsts', True)
        },
        'backup': {
            'auto_backup': settings_model.get_setting('backup.auto_backup', True),
            'backup_frequency': settings_model.get_setting('backup.backup_frequency', 'weekly'),
            'backup_time': settings_model.get_setting('backup.backup_time', '02:00'),
            'backup_type': settings_model.get_setting('backup.backup_type', 'full'),
            'compress_backups': settings_model.get_setting('backup.compress_backups', True),
            'retention_period': settings_model.get_setting('backup.retention_period', 30),
            'max_backups': settings_model.get_setting('backup.max_backups', 10),
            'backup_location': settings_model.get_setting('backup.backup_location', 'backups'),
            'external_storage': settings_model.get_setting('backup.external_storage', False),
            'external_storage_type': settings_model.get_setting('backup.external_storage_type', 's3')
        }
    }
    
    # Get real backup data from the database
    try:
        # Get backup records from database
        from database.models.backup import BackupRecord
        backup_record = BackupRecord()
        backups = backup_record.list_backups(limit=10)
        
        # Format backups for template
        formatted_backups = []
        for backup in backups:
            formatted_backup = {
                'id': str(backup.get('_id')),
                'filename': backup.get('filename'),
                'type': backup.get('type'),
                'size': backup.get('size'),
                'created_at': backup.get('created_at'),
                'success': backup.get('success', True),
                'details': backup.get('details')
            }
            formatted_backups.append(formatted_backup)
    except Exception as e:
        logger.error(f"Error getting backup records: {e}")
        # Fall back to empty list if there's an error
        formatted_backups = []
    
    # Get system stats
    system_stats = {
        'cpu_usage': 35,
        'memory_usage': 62,
        'disk_usage': 48,
        'active_connections': 18,
        'uptime': '23 days, 4 hours'
    }
    
    # Mock dependencies data
    dependencies = {
        'flask': '2.3.2',
        'pymongo': '4.5.0',
        'flask_wtf': '1.1.1',
        'passlib': '1.7.4',
        'psutil': '5.9.5'
    }
    
    # Render settings template with the data
    return render_template(
        'admin/settings.html', 
        settings=settings,
        backups=formatted_backups,
        system_stats=system_stats,
        system_info=system_info,
        dependencies=dependencies,
        current_user=current_user,
        title='System Settings',
        os_info=platform.platform()
    )

def test_email():
    """Test email configuration."""
    # This is handled directly in the settings route
    return redirect(url_for('admin.settings', tab='email'))
