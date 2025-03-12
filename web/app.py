"""
Flask web application for Travian Whispers.
"""
import os
import logging
import datetime
from datetime import timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web.app')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # Only use secure cookies in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Initialize static and templates directories
def setup_directories():
    """Ensure the static and templates directories exist."""
    os.makedirs(os.path.join(app.root_path, 'static'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'img'), exist_ok=True)
    
    # Create a simple CSS file if it doesn't exist
    css_path = os.path.join(app.root_path, 'static', 'css', 'style.css')
    if not os.path.exists(css_path):
        with open(css_path, 'w') as f:
            f.write("""
/* Base styles for Travian Whispers */
:root {
    --primary-color: #3a6ea5;
    --secondary-color: #ff9a3c;
    --dark-color: #344055;
    --light-color: #f4f4f9;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}
""")

# Run setup on application initialization
setup_directories()

# Mock user class for development
class User:
    def __init__(self, id=None, username=None, email=None, role=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.is_authenticated = False

# Connect to database (if available)
try:
    from database.mongodb import MongoDB
    db = MongoDB()
    db_connected = db.connect()
    if db_connected:
        logger.info("Connected to MongoDB successfully")
    else:
        logger.warning("Failed to connect to MongoDB. Some features may be limited.")
except ImportError:
    logger.warning("MongoDB module not found. Running in development mode.")
    db_connected = False

# Mock current user for templates
@app.context_processor
def inject_user():
    """Inject current_user into templates."""
    user = User()
    if 'user_id' in session:
        user.id = session['user_id']
        user.username = session.get('username', 'User')
        user.email = session.get('email', '')
        user.role = session.get('role', 'user')
        user.is_authenticated = True
    return {'current_user': user}

def init_error_handlers(app):
    """
    Initialize error handlers for Flask application.
    """
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "Resource not found"}), 404
        return render_template('errors/404.html', title='Page Not Found'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "Internal server error"}), 500
        return render_template('errors/500.html', title='Server Error'), 500

# Initialize error handlers
init_error_handlers(app)

# Main routes
@app.route('/')
def index():
    """Home page route."""
    return render_template('index.html', title='Travian Whispers - Advanced Travian Automation')

@app.route('/dashboard')
def dashboard():
    """User dashboard route."""
    if 'user_id' not in session:
        flash('Please log in to access your dashboard', 'warning')
        return redirect(url_for('login'))
    return render_template('user/dashboard.html', title='Dashboard')

@app.route('/profile')
def profile():
    """User profile route."""
    if 'user_id' not in session:
        flash('Please log in to access your profile', 'warning')
        return redirect(url_for('login'))
    
    try:
        # Mock user data for development
        # In production, you would get this from your database
        user_profile = {
            "username": session.get('username', 'User'),
            "email": session.get('email', 'user@example.com'),
            "subscription": {
                "status": "active",
                "start_date": "2025-02-15",
                "end_date": "2025-03-15",
            },
            "settings": {
                "notification_email": True,
                "auto_renew": True
            },
            "travian_credentials": {
                "username": "travian_user",
                "password": "********",
                "server": "ts1.x1.international.travian.com",
                "tribe": "Romans"
            }
        }
        
        return render_template('user/profile.html', 
                              title='Profile', 
                              user_profile=user_profile)
    except Exception as e:
        # Log the error
        logger.error(f"Error rendering profile page: {str(e)}")
        # Return a user-friendly error page
        return render_template('errors/500.html', title='Server Error'), 500

@app.route('/travian_settings', methods=['GET', 'POST'])
def travian_settings():
    """Travian settings route."""
    if 'user_id' not in session:
        flash('Please log in to access Travian settings', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'account_settings':
            # Handle Travian account form
            travian_username = request.form.get('travian_username')
            travian_password = request.form.get('travian_password')
            travian_server = request.form.get('travian_server')
            travian_tribe = request.form.get('travian_tribe')
            
            # Update user's Travian credentials
            # In production, you would update the database here
            
            flash('Travian account settings saved successfully!', 'success')
            
        elif form_type == 'bot_settings':
            # Handle bot behavior settings form
            randomization = request.form.get('randomization')
            farming_interval = request.form.get('farming_interval')
            training_interval = request.form.get('training_interval')
            captcha_notification = 'captcha_notification' in request.form
            auto_restart = 'auto_restart' in request.form
            
            # Update user's bot settings
            # In production, you would update the database here
            
            flash('Bot settings saved successfully!', 'success')
            
        elif form_type == 'browser_settings':
            # Handle browser settings form
            browser_type = request.form.get('browser_type')
            headless = 'headless' in request.form
            save_session = 'save_session' in request.form
            user_agent = request.form.get('user_agent')
            
            # Update user's browser settings
            # In production, you would update the database here
            
            flash('Browser settings saved successfully!', 'success')
        
        return redirect(url_for('travian_settings'))
    
    # Mock user data for development
    user_profile = {
        "travian_credentials": {
            "username": "travian_user",
            "password": "********",
            "server": "ts1.x1.international.travian.com",
            "tribe": "Romans"
        },
        "settings": {
            "randomization": "medium",
            "farming_interval": 30,
            "training_interval": 60,
            "captcha_notification": True,
            "auto_restart": True,
            "browser_type": "chrome",
            "headless": False,
            "save_session": True,
            "user_agent": ""
        }
    }
    
    return render_template('user/travian_settings.html', title='Travian Settings', user_profile=user_profile)

# Admin routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html', title='Admin Dashboard')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # For development: mock login
        if db_connected:
            try:
                from auth.login import login_user
                success, message, token, user_data = login_user(username, password)
                
                if success and user_data:
                    session['user_id'] = user_data.get('id')
                    session['username'] = user_data.get('username')
                    session['email'] = user_data.get('email')
                    session['role'] = user_data.get('role', 'user')
                    
                    flash(message, 'success')
                    next_url = request.args.get('next', url_for('dashboard'))
                    return redirect(next_url)
                else:
                    flash(message, 'danger')
            except Exception as e:
                logger.error(f"Login error: {e}")
                flash('An error occurred during login. Please try again.', 'danger')
        else:
            # Mock login for development without database
            if username and password:
                session['user_id'] = '1'
                session['username'] = username
                session['email'] = f"{username}@example.com"
                session['role'] = 'admin' if username == 'admin' else 'user'
                
                flash('Login successful!', 'success')
                next_url = request.args.get('next', url_for('dashboard'))
                return redirect(next_url)
            else:
                flash('Invalid username or password', 'danger')
    
    # GET request: show login form
    return render_template('auth/login.html', title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if db_connected:
            try:
                from auth.registration import register_user
                verification_url = url_for('verify_email', token='TOKEN_PLACEHOLDER', _external=True)
                verification_url = verification_url.replace('TOKEN_PLACEHOLDER', '')
                
                success, message, user_data = register_user(
                    username, 
                    email, 
                    password, 
                    confirm_password, 
                    verification_url
                )
                
                if success:
                    flash(message, 'success')
                    return redirect(url_for('login'))
                else:
                    flash(message, 'danger')
            except Exception as e:
                logger.error(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
        else:
            # Mock registration for development without database
            if username and email and password and password == confirm_password:
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please check your inputs.', 'danger')
    
    # GET request: show registration form
    return render_template('auth/register.html', title='Register')

@app.route('/logout')
def logout():
    """User logout route."""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password route."""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if db_connected and email:
            try:
                from auth.password_reset import request_password_reset
                
                # Generate reset URL
                reset_url = url_for('reset_password', token='TOKEN_PLACEHOLDER', _external=True)
                reset_url = reset_url.replace('TOKEN_PLACEHOLDER', '')
                
                success, message = request_password_reset(email, reset_url)
                flash(message, 'info')
                return redirect(url_for('login'))
            except Exception as e:
                logger.error(f"Password reset request error: {e}")
                flash('An error occurred. Please try again later.', 'danger')
        else:
            # Mock for development without database
            flash('If your email exists in our system, you will receive password reset instructions.', 'info')
            return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html', title='Forgot Password')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password route."""
    token = request.args.get('token')
    
    if not token:
        flash('Invalid password reset link', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if db_connected:
            try:
                from auth.password_reset import reset_password as do_reset_password
                
                success, message = do_reset_password(token, new_password, confirm_password)
                
                if success:
                    flash(message, 'success')
                    return redirect(url_for('login'))
                else:
                    flash(message, 'danger')
            except Exception as e:
                logger.error(f"Password reset error: {e}")
                flash('An error occurred. Please try again later.', 'danger')
        else:
            # Mock for development without database
            if new_password and new_password == confirm_password:
                flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Passwords do not match', 'danger')
    
    # GET request: show reset password form
    return render_template('auth/reset_password.html', title='Reset Password', token=token)

@app.route('/verify-email')
def verify_email():
    """Email verification route."""
    token = request.args.get('token')
    
    if not token:
        flash('Invalid verification link', 'danger')
        return redirect(url_for('login'))
    
    if db_connected:
        try:
            from auth.verification import verify_email_token
            
            success, message, user_data = verify_email_token(token)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            flash('An error occurred during verification. Please try again later.', 'danger')
    else:
        # Mock for development without database
        flash('Email verified successfully! You can now log in.', 'success')
    
    return redirect(url_for('login'))

# API routes
@app.route('/api/health')
def health_check():
    """API health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "timestamp": str(datetime.datetime.now())
    })

# PayPal webhook
@app.route('/api/webhooks/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events."""
    if not db_connected:
        return jsonify({"success": False, "message": "Database not connected"}), 503
    
    try:
        from payment.paypal import verify_webhook_signature, handle_webhook_event
        
        # Get request data
        request_body = request.get_data()
        headers = request.headers
        
        # Verify signature
        if not verify_webhook_signature(request_body, headers):
            logger.error("Invalid PayPal webhook signature")
            return jsonify({"success": False, "message": "Invalid signature"}), 400
        
        # Process the event
        event_data = request.json
        event_type = event_data.get('event_type')
        
        if not event_type:
            return jsonify({"success": False, "message": "Missing event type"}), 400
        
        success = handle_webhook_event(event_type, event_data)
        
        if success:
            logger.info(f"Successfully handled PayPal webhook event: {event_type}")
            return jsonify({"success": True, "message": "Event processed successfully"}), 200
        else:
            logger.error(f"Failed to process PayPal webhook event: {event_type}")
            return jsonify({"success": False, "message": "Event processing failed"}), 500
    except ImportError:
        logger.error("PayPal module not found")
        return jsonify({"success": False, "message": "Payment module not available"}), 501
    except Exception as e:
        logger.error(f"Error processing PayPal webhook: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

# Additional user routes
@app.route('/villages')
def villages():
    """Villages management route."""
    if 'user_id' not in session:
        flash('Please log in to access your villages', 'warning')
        return redirect(url_for('login'))
    return render_template('user/villages.html', title='Villages')

@app.route('/auto_farm')
def auto_farm():
    """Auto-farm management route."""
    if 'user_id' not in session:
        flash('Please log in to access auto-farm', 'warning')
        return redirect(url_for('login'))
    return render_template('user/auto_farm.html', title='Auto-Farm')

@app.route('/troop_trainer')
def troop_trainer():
    """Troop trainer management route."""
    if 'user_id' not in session:
        flash('Please log in to access troop trainer', 'warning')
        return redirect(url_for('login'))
    return render_template('user/troop_trainer.html', title='Troop Trainer')

@app.route('/activity_logs')
def activity_logs():
    """Activity logs route."""
    if 'user_id' not in session:
        flash('Please log in to access activity logs', 'warning')
        return redirect(url_for('login'))
    return render_template('user/activity_logs.html', title='Activity Logs')

@app.route('/subscription')
def subscription():
    """Subscription management route."""
    if 'user_id' not in session:
        flash('Please log in to access subscription settings', 'warning')
        return redirect(url_for('login'))
    return render_template('user/subscription.html', title='Subscription')

@app.route('/support')
def support():
    """Support and help route."""
    if 'user_id' not in session:
        flash('Please log in to access support', 'warning')
        return redirect(url_for('login'))
    return render_template('user/support.html', title='Help & Support')

# Run the application
if __name__ == "__main__":
    app.run(debug=True)