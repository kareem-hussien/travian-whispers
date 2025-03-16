"""
Authentication routes for Travian Whispers web application.
This module defines the blueprint for authentication-related routes.
"""
import logging
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app
)

from auth.login import login_user, logout_user
from auth.registration import register_user
from auth.verification import verify_email_token, resend_verification_email
from auth.password_reset import (
    request_password_reset, validate_reset_token, reset_password
)
from web.utils.decorators import redirect_if_authenticated

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@redirect_if_authenticated
def login():
    """Login route."""
    # Default values
    username = ''
    
    # Process form submission
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        remember_me = 'remember' in request.form
        
        # Authenticate user
        success, message, token, user_data = login_user(username, password, remember_me)
        
        if success:
            # Store user data in session
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            session['email'] = user_data['email']
            session['role'] = user_data['role']
            session['token'] = token
            
            # Log successful login
            logger.info(f"User '{username}' logged in successfully")
            
            # Redirect to requested page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            # Redirect to appropriate dashboard based on role
            if user_data['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            # Flash error message
            flash(message, 'danger')
            logger.warning(f"Failed login attempt for '{username}': {message}")
    
    # Render login template
    return render_template('auth/login.html', username=username, title='Login')


@auth_bp.route('/logout')
def logout():
    """Logout route."""
    # Log the logout
    if 'username' in session:
        logger.info(f"User '{session['username']}' logged out")
    
    # Clear session
    logout_user()
    session.clear()
    
    # Flash success message and redirect to login
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@redirect_if_authenticated
def register():
    """User registration route."""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Check if terms accepted
        if 'terms' not in request.form:
            flash('You must accept the Terms and Conditions to register.', 'danger')
            return render_template(
                'auth/register.html', 
                username=username, 
                email=email, 
                title='Register'
            )
        
        # Generate verification URL
        base_url = request.host_url.rstrip('/') + url_for('auth.verify_email', token='')
        
        # Register user
        success, message, user_data = register_user(
            username, 
            email, 
            password, 
            confirm_password, 
            base_url
        )
        
        if success:
            # Flash success message
            flash(message, 'success')
            logger.info(f"New user registered: {username} ({email})")
            
            # Redirect to login page
            return redirect(url_for('auth.login'))
        else:
            # Flash error message
            flash(message, 'danger')
            logger.warning(f"Registration failed for {username} ({email}): {message}")
    
    # Render registration template
    return render_template('auth/register.html', title='Register')


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification route."""
    # Verify email token
    success, message, user_data = verify_email_token(token)
    
    if success:
        # Flash success message
        flash(message, 'success')
        logger.info(f"Email verified for user: {user_data['username']}")
        
        # Redirect to login page
        return redirect(url_for('auth.login'))
    else:
        # Flash error message
        flash(message, 'danger')
        logger.warning(f"Email verification failed: {message}")
        
        # Render verification failed template
        return render_template('auth/verification_failed.html', title='Verification Failed')


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend verification email route."""
    if request.method == 'POST':
        email = request.form.get('email', '')
        
        # Generate verification URL
        base_url = request.host_url.rstrip('/') + url_for('auth.verify_email', token='')
        
        # Resend verification email
        try:
            success, message = resend_verification_email(email, base_url)
            
            if success:
                # Flash success message
                flash(message, 'success')
                logger.info(f"Verification email resent to: {email}")
                
                # Redirect to login page
                return redirect(url_for('auth.login'))
            else:
                # Flash error message
                flash(message, 'danger')
                logger.warning(f"Failed to resend verification email to {email}: {message}")
        except Exception as e:
            # Flash error message
            flash(f"An error occurred: {str(e)}", 'danger')
            logger.error(f"Error resending verification email to {email}: {str(e)}")
    
    # Render resend verification template
    return render_template('auth/resend_verification.html', title='Resend Verification Email')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password route."""
    if request.method == 'POST':
        email = request.form.get('email', '')
        
        # Generate reset URL
        base_url = request.host_url.rstrip('/') + url_for('auth.reset_password', token='')
        
        # Request password reset
        try:
            success, message = request_password_reset(email, base_url)
            
            # Flash appropriate message
            if success:
                flash(message, 'info')
                logger.info(f"Password reset requested for: {email}")
            else:
                flash(message, 'danger')
                logger.warning(f"Password reset request failed for {email}: {message}")
            
            # Redirect to login page
            return redirect(url_for('auth.login'))
        except Exception as e:
            # Flash error message
            flash(f"An error occurred: {str(e)}", 'danger')
            logger.error(f"Error processing password reset request for {email}: {str(e)}")
    
    # Render forgot password template
    return render_template('auth/forgot_password.html', title='Forgot Password')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_route():
    """Reset password route."""
    token = request.args.get('token', '')
    
    # Validate token
    is_valid, user_data = validate_reset_token(token)
    
    if not is_valid:
        # Flash error message
        flash('Invalid or expired password reset token.', 'danger')
        logger.warning(f"Invalid password reset token: {token}")
        
        # Redirect to forgot password page
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        # Get form data
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Reset password
        try:
            success, message = reset_password(token, new_password, confirm_password)
            
            if success:
                # Flash success message
                flash(message, 'success')
                logger.info(f"Password reset successful for user: {user_data['username']}")
                
                # Redirect to login page
                return redirect(url_for('auth.login'))
            else:
                # Flash error message
                flash(message, 'danger')
                logger.warning(f"Password reset failed: {message}")
        except Exception as e:
            # Flash error message
            flash(f"An error occurred: {str(e)}", 'danger')
            logger.error(f"Error resetting password: {str(e)}")
    
    # Render reset password template
    return render_template(
        'auth/reset_password.html', 
        token=token, 
        email=user_data['email'], 
        title='Reset Password'
    )
