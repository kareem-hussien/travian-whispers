"""
Flask web application for Travian Whispers.
"""
import os
import logging
import datetime
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import config

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web.app')

def create_app(test_config=None):
    """Create and configure the Flask application."""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Configure the app
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=config.SECRET_KEY,
            PERMANENT_SESSION_LIFETIME=timedelta(days=30)
        )
    else:
        app.config.from_mapping(test_config)
    
    # Initialize static and templates directories
    setup_directories(app)
    
    # Initialize error handlers
    init_error_handlers(app)
    
    # Register routes
    register_routes(app)
    
    # Return the configured app
    return app

def setup_directories(app):
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
        
        # Log traceback for better debugging
        import traceback
        trace = traceback.format_exc()
        logger.error(f"Traceback: {trace}")
        
        return render_template('errors/500.html', title='Server Error'), 500

def register_routes(app):
    """Register all routes with the Flask application."""
    
    # Authentication helpers
    def check_authenticated():
        """Check if user is authenticated."""
        if 'user_id' not in session:
            return False, None
        
        # Import here to avoid circular imports
        from database.models.user import User
        user_model = User()
        user = user_model.get_user_by_id(session['user_id'])
        
        if user is None:
            # Clear invalid session
            session.clear()
            return False, None
        
        user_data = {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
        
        return True, user_data
    
    # Authentication decorators
    def login_required(view_func):
        """Decorator to require login for views."""
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('login', next=request.path))
            return view_func(*args, **kwargs)
        return wrapped_view
    
    def admin_required(view_func):
        """Decorator to require admin role for views."""
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('login', next=request.path))
            
            if session.get('role') != 'admin':
                flash('Admin access required', 'danger')
                return redirect(url_for('dashboard'))
            
            return view_func(*args, **kwargs)
        return wrapped_view
    
    # Context processor for user data
    @app.context_processor
    def inject_user():
        """Inject user data into all templates."""
        is_authenticated, user_data = check_authenticated()
        
        if is_authenticated:
            user = {
                'is_authenticated': True,
                'id': user_data['id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role']
            }
        else:
            user = {
                'is_authenticated': False,
                'id': None,
                'username': None,
                'email': None,
                'role': None
            }
        
        return {'current_user': user}
    
    # Main routes
    @app.route('/')
    def index():
        """Home page route."""
        return render_template('index.html', title='Travian Whispers - Advanced Travian Automation')
    
    # Auth routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login route."""
        if request.method == 'POST':
            username_or_email = request.form.get('username', '')
            password = request.form.get('password', '')
            remember_me = 'remember' in request.form
            
            try:
                # Use the login_user function
                from auth.login import login_user
                success, message, token, user_data = login_user(username_or_email, password, remember_me)
                
                if success:
                    # Store user info in session
                    session['user_id'] = user_data['id']
                    session['username'] = user_data['username']
                    session['email'] = user_data['email']
                    session['role'] = user_data['role']
                    
                    # Handle remember me option
                    if remember_me:
                        session.permanent = True
                    
                    flash('Login successful!', 'success')
                    
                    # Redirect based on user role
                    if user_data['role'] == 'admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('dashboard'))
                else:
                    flash(message, 'danger')
                    return render_template('auth/login.html', title='Login', username=username_or_email)
            except Exception as e:
                app.logger.error(f"Login error: {str(e)}")
                flash('An error occurred during login. Please try again.', 'danger')
                return render_template('auth/login.html', title='Login', username=username_or_email)
        
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
            
            # Validate inputs
            if not username or not email or not password:
                flash('All fields are required', 'danger')
                return render_template('auth/register.html', title='Register')
                
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return render_template('auth/register.html', title='Register')
            
            # Generate verification URL (for email)
            verification_url = url_for('verify_email', token='TOKEN', _external=True)
            verification_url = verification_url.replace('TOKEN', '')  # The token will be added by the registration function
            
            # Use the actual registration function
            from auth.registration import register_user
            try:
                success, message, user_data = register_user(username, email, password, confirm_password, verification_url)
                
                if success:
                    flash(message, 'success')
                    return redirect(url_for('login'))
                else:
                    flash(message, 'danger')
                    return render_template('auth/register.html', title='Register')
            except Exception as e:
                logger.error(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again later.', 'danger')
                return render_template('auth/register.html', title='Register')
        
        # GET request: show registration form
        return render_template('auth/register.html', title='Register')
    
    @app.route('/verify-email')
    def verify_email():
        """Email verification route."""
        token = request.args.get('token')
        
        if not token:
            flash('Invalid verification link - missing token', 'danger')
            logger.error("Verification attempt with no token")
            return redirect(url_for('login'))
        
        # Debug token
        logger.info(f"Attempting to verify email with token: {token}")
        
        try:
            # Use the actual verification function
            from auth.verification import verify_email_token
            success, message, user_data = verify_email_token(token)
            
            # Log the result
            logger.info(f"Verification result: success={success}, message={message}")
            
            flash(message, 'success' if success else 'danger')
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            import traceback
            logger.error(traceback.format_exc())  # Log the full traceback
            flash('An error occurred during verification. Please try again or contact support.', 'danger')
        
        return redirect(url_for('login'))
    
    @app.route('/logout')
    def logout():
        """User logout route."""
        try:
            # Log before logout
            username = session.get('username', 'Unknown')
            app.logger.info(f"User logging out: {username}")
            
            # Import and call the logout function
            from auth.login import logout_user
            logout_user()
            
            flash('You have been logged out successfully', 'success')
        except Exception as e:
            app.logger.error(f"Logout error: {str(e)}")
            flash('An error occurred during logout', 'warning')
        
        # Always redirect to index, even if there was an error
        return redirect(url_for('index'))
    
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        """Forgot password route."""
        if request.method == 'POST':
            email = request.form.get('email')
            
            if not email:
                flash('Email is required', 'danger')
                return render_template('auth/forgot_password.html', title='Forgot Password')
            
            # Generate reset URL
            reset_url_base = url_for('reset_password', token='TOKEN', _external=True)
            reset_url_base = reset_url_base.replace('TOKEN', '')  # The token will be added by the request function
            
            # Use the actual password reset request function
            from auth.password_reset import request_password_reset
            success, message = request_password_reset(email, reset_url_base)
            
            flash(message, 'info')
            return redirect(url_for('login'))
        
        return render_template('auth/forgot_password.html', title='Forgot Password')
    
    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password():
        """Reset password route."""
        token = request.args.get('token')
        
        if not token:
            flash('Invalid password reset link', 'danger')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Use the actual password reset function
            from auth.password_reset import reset_password as do_reset_password
            success, message = do_reset_password(token, new_password, confirm_password)
            
            flash(message, 'success' if success else 'danger')
            if success:
                return redirect(url_for('login'))
        
        # Verify token is valid before showing the form
        from auth.password_reset import validate_reset_token
        is_valid, user_data = validate_reset_token(token)
        
        if not is_valid:
            flash('Invalid or expired password reset token', 'danger')
            return redirect(url_for('login'))
        
        return render_template('auth/reset_password.html', title='Reset Password', token=token)
    
    # Dashboard route
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """User dashboard route."""
        # Get user data from database
        from database.models.user import User
        user_model = User()
        user = user_model.get_user_by_id(session['user_id'])
        
        if user is None:
            # Invalid user ID in session
            session.clear()
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('login'))
        
        # Get subscription plan details if any
        subscription_data = {
            'status': user['subscription']['status'],
            'plan_name': 'No Plan',
            'end_date': None
        }
        
        if user['subscription']['planId'] is not None:
            from database.models.subscription import SubscriptionPlan
            plan_model = SubscriptionPlan()
            plan = plan_model.get_plan_by_id(user['subscription']['planId'])
            
            if plan is not None:
                subscription_data['plan_name'] = plan['name']
                subscription_data['end_date'] = user['subscription']['endDate'].strftime('%Y-%m-%d') if user['subscription']['endDate'] else None
        
        # User profile data for the dashboard
        user_profile = {
            'subscription': subscription_data,
            'villages': user.get('villages', []),
            'tasks': []  # This would be populated from active tasks
        }
        
        return render_template('user/dashboard.html', title='Dashboard', user_profile=user_profile)

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """User profile route."""
        if request.method == 'POST':
            form_type = request.form.get('form_type')
            
            if form_type == 'profile':
                # Process profile update
                flash('Profile updated successfully!', 'success')
            elif form_type == 'password':
                # Process password change
                flash('Password changed successfully!', 'success')
            
            return redirect(url_for('profile'))
        
        # Mock user profile data
        user_profile = {
            'username': session.get('username', 'User'),
            'email': session.get('email', 'user@example.com'),
            'settings': {
                'notification_email': True,
                'auto_renew': False
            },
            'subscription': {
                'status': 'active',
                'plan_name': 'Standard Plan',
                'start_date': '2025-03-12',
                'end_date': '2025-04-12'
            }
        }
        
        return render_template('user/profile.html', title='Profile', user_profile=user_profile)

    @app.route('/travian_settings', methods=['GET', 'POST'])
    @login_required
    def travian_settings():
        """Travian settings route."""
        if request.method == 'POST':
            # Process Travian settings update
            flash('Travian settings updated successfully!', 'success')
            return redirect(url_for('travian_settings'))
        
        # Mock user profile data
        user_profile = {
            'travian_credentials': {
                'username': 'travian_user',
                'server': 'ts1.x1.international.travian.com',
                'tribe': 'Romans'
            }
        }
        
        return render_template('user/travian_settings.html', title='Travian Settings', user_profile=user_profile)

    @app.route('/villages')
    @login_required
    def villages():
        """Villages management route."""
        # Mock villages data
        villages_data = [
            {'id': 1, 'name': 'Main Village', 'coordinates': '(24, -35)', 'population': 320, 'status': 'active'},
            {'id': 2, 'name': 'Second Village', 'coordinates': '(22, -40)', 'population': 215, 'status': 'active'}
        ]
        
        return render_template('user/villages.html', title='Villages Management', villages=villages_data)

    @app.route('/auto_farm')
    @login_required
    def auto_farm():
        """Auto farm management route."""
        # Mock auto farm data
        auto_farm_data = {
            'status': 'active',
            'interval': 45,
            'last_run': '2025-03-12 15:30:45',
            'next_run': '2025-03-12 16:15:45',
            'villages': [
                {'id': 1, 'name': 'Main Village', 'status': 'active'},
                {'id': 2, 'name': 'Second Village', 'status': 'active'}
            ]
        }
        
        return render_template('user/auto_farm.html', title='Auto Farm', auto_farm=auto_farm_data)

    @app.route('/troop_trainer')
    @login_required
    def troop_trainer():
        """Troop trainer management route."""
        # Mock troop trainer data
        troop_trainer_data = {
            'status': 'paused',
            'tribe': 'Romans',
            'troops': [
                {'name': 'Legionnaire', 'quantity': 50, 'status': 'training'},
                {'name': 'Praetorian', 'quantity': 30, 'status': 'queued'},
                {'name': 'Imperian', 'quantity': 20, 'status': 'pending'}
            ],
            'villages': [
                {'id': 1, 'name': 'Main Village', 'status': 'active'},
                {'id': 2, 'name': 'Second Village', 'status': 'paused'}
            ]
        }
        
        return render_template('user/troop_trainer.html', title='Troop Trainer', trainer=troop_trainer_data)

    @app.route('/activity_logs')
    @login_required
    def activity_logs():
        """Activity logs route."""
        # Mock activity logs data
        logs = [
            {'date': '2025-03-12 15:30:45', 'activity': 'Auto-Farm', 'details': 'Sent farm lists from Main Village', 'status': 'success'},
            {'date': '2025-03-12 14:15:22', 'activity': 'Troop Training', 'details': 'Trained 50 Legionnaires in Main Village', 'status': 'success'},
            {'date': '2025-03-12 12:30:10', 'activity': 'Auto-Farm', 'details': 'Sent farm lists from Second Village', 'status': 'success'},
            {'date': '2025-03-12 11:05:38', 'activity': 'System', 'details': 'Bot started after maintenance', 'status': 'info'},
            {'date': '2025-03-12 10:45:15', 'activity': 'System', 'details': 'Scheduled maintenance began', 'status': 'warning'}
        ]
        
        return render_template('user/activity_logs.html', title='Activity Logs', logs=logs)

    @app.route('/subscription')
    @login_required
    def subscription():
        """Subscription management route."""
        # Mock subscription data
        subscription_data = {
            'current_plan': 'Standard Plan',
            'status': 'active',
            'start_date': '2025-03-12',
            'end_date': '2025-04-12',
            'auto_renew': False,
            'payment_method': 'PayPal',
            'payment_history': [
                {'date': '2025-03-12', 'amount': '$9.99', 'method': 'PayPal', 'status': 'completed'},
                {'date': '2025-02-12', 'amount': '$9.99', 'method': 'PayPal', 'status': 'completed'},
                {'date': '2025-01-12', 'amount': '$9.99', 'method': 'PayPal', 'status': 'completed'}
            ],
            'available_plans': [
                {'id': 1, 'name': 'Basic Plan', 'price': '$4.99', 'features': ['Auto-Farm feature', 'Support for 2 villages', '1 concurrent task']},
                {'id': 2, 'name': 'Standard Plan', 'price': '$9.99', 'features': ['Auto-Farm feature', 'Troop training', 'Support for 5 villages', '2 concurrent tasks']},
                {'id': 3, 'name': 'Premium Plan', 'price': '$19.99', 'features': ['Auto-Farm feature', 'Troop training', 'Support for 15 villages', '5 concurrent tasks', 'Advanced features']}
            ]
        }
        
        return render_template('user/subscription.html', title='Subscription Management', subscription=subscription_data)

    @app.route('/support')
    @login_required
    def support():
        """Help and support route."""
        return render_template('user/support.html', title='Help & Support')

    # Admin routes
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Admin dashboard route."""
        # Mock admin dashboard data
        admin_data = {
            'total_users': 245,
            'active_users': 189,
            'expired_users': 56,
            'total_revenue': '$2,345.67',
            'recent_transactions': [
                {'id': 'TX12345', 'user': 'user1', 'amount': '$9.99', 'date': '2025-03-12', 'status': 'completed'},
                {'id': 'TX12344', 'user': 'user2', 'amount': '$19.99', 'date': '2025-03-12', 'status': 'completed'},
                {'id': 'TX12343', 'user': 'user3', 'amount': '$4.99', 'date': '2025-03-11', 'status': 'completed'},
                {'id': 'TX12342', 'user': 'user4', 'amount': '$9.99', 'date': '2025-03-11', 'status': 'pending'},
                {'id': 'TX12341', 'user': 'user5', 'amount': '$9.99', 'date': '2025-03-10', 'status': 'completed'}
            ]
        }
        
        return render_template('admin/dashboard.html', title='Admin Dashboard', admin_data=admin_data)

# No app creation or route definitions outside of functions
# This ensures no 'app' variables are used at module level