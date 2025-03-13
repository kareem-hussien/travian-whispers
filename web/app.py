"""
Flask web application for Travian Whispers.
"""
import os
import logging
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('web.app')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

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
    
    # Mock data for the dashboard
    user_profile = {
        'subscription': {
            'status': 'active',
            'plan_name': 'Standard Plan',
            'end_date': '2025-04-12'
        },
        'villages': [
            {'name': 'Main Village', 'coordinates': '(24, -35)', 'population': 320},
            {'name': 'Second Village', 'coordinates': '(22, -40)', 'population': 215}
        ],
        'tasks': [
            {'name': 'Auto-Farming', 'status': 'active', 'duration': '3d 05h 12m'},
            {'name': 'Troop Training', 'status': 'paused', 'duration': '1d 12h 45m'}
        ]
    }
    
    return render_template('user/dashboard.html', title='Dashboard', user_profile=user_profile)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    """User profile route."""
    if 'user_id' not in session:
        flash('Please log in to access your profile', 'warning')
        return redirect(url_for('login'))
    
    # Process form submissions
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
def travian_settings():
    """Travian settings route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
    # Process form submissions
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
def villages():
    """Villages management route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
    # Mock villages data
    villages_data = [
        {'id': 1, 'name': 'Main Village', 'coordinates': '(24, -35)', 'population': 320, 'status': 'active'},
        {'id': 2, 'name': 'Second Village', 'coordinates': '(22, -40)', 'population': 215, 'status': 'active'}
    ]
    
    return render_template('user/villages.html', title='Villages Management', villages=villages_data)

@app.route('/auto_farm')
def auto_farm():
    """Auto farm management route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
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
def troop_trainer():
    """Troop trainer management route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
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
def activity_logs():
    """Activity logs route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
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
def subscription():
    """Subscription management route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
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
def support():
    """Help and support route."""
    if 'user_id' not in session:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('login'))
    
    return render_template('user/support.html', title='Help & Support')

# Admin routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
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

@app.route('/admin/users')
def admin_users():
    """Admin users management route."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    # Mock users data
    users_data = [
        {'id': 1, 'username': 'user1', 'email': 'user1@example.com', 'role': 'user', 'status': 'active', 'subscription': 'Standard', 'joined': '2025-02-15'},
        {'id': 2, 'username': 'user2', 'email': 'user2@example.com', 'role': 'user', 'status': 'active', 'subscription': 'Premium', 'joined': '2025-02-20'},
        {'id': 3, 'username': 'user3', 'email': 'user3@example.com', 'role': 'user', 'status': 'inactive', 'subscription': 'Basic', 'joined': '2025-03-01'},
        {'id': 4, 'username': 'admin', 'email': 'admin@example.com', 'role': 'admin', 'status': 'active', 'subscription': 'Premium', 'joined': '2025-01-10'}
    ]
    
    return render_template('admin/users.html', title='User Management', users=users_data)

@app.route('/admin/subscriptions')
def admin_subscriptions():
    """Admin subscription plans management route."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    # Mock subscription plans data
    plans_data = [
        {'id': 1, 'name': 'Basic Plan', 'price': '$4.99', 'users': 78, 'revenue': '$389.22'},
        {'id': 2, 'name': 'Standard Plan', 'price': '$9.99', 'users': 95, 'revenue': '$949.05'},
        {'id': 3, 'name': 'Premium Plan', 'price': '$19.99', 'users': 16, 'revenue': '$319.84'}
    ]
    
    return render_template('admin/subscriptions.html', title='Subscription Plans', plans=plans_data)

@app.route('/admin/transactions')
def admin_transactions():
    """Admin transactions management route."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    # Mock transactions data
    transactions_data = [
        {'id': 'TX12345', 'user': 'user1', 'plan': 'Standard', 'amount': '$9.99', 'date': '2025-03-12', 'status': 'completed'},
        {'id': 'TX12344', 'user': 'user2', 'plan': 'Premium', 'amount': '$19.99', 'date': '2025-03-12', 'status': 'completed'},
        {'id': 'TX12343', 'user': 'user3', 'plan': 'Basic', 'amount': '$4.99', 'date': '2025-03-11', 'status': 'completed'},
        {'id': 'TX12342', 'user': 'user4', 'plan': 'Standard', 'amount': '$9.99', 'date': '2025-03-11', 'status': 'pending'},
        {'id': 'TX12341', 'user': 'user5', 'plan': 'Standard', 'amount': '$9.99', 'date': '2025-03-10', 'status': 'completed'}
    ]
    
    return render_template('admin/transactions.html', title='Transactions', transactions=transactions_data)

@app.route('/admin/settings')
def admin_settings():
    """Admin system settings route."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/settings.html', title='System Settings')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # For development: mock login
        if username and password:
            # In production, this would validate against the database
            session['user_id'] = '1'
            session['username'] = username
            session['email'] = f"{username}@example.com"
            session['role'] = 'admin' if username == 'admin' else 'user'
            
            flash('Login successful!', 'success')
            next_url = request.args.get('next', url_for('dashboard'))
            return redirect(next_url)
        else:
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html', title='Login')
    
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
        
        # For development: mock registration
        if username and email and password and password == confirm_password:
            # In production, this would save to the database
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please check your inputs.', 'danger')
            return render_template('auth/register.html', title='Register')
    
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
        if email:
            # In production, this would send a password reset email
            flash('If your email exists in our system, you will receive password reset instructions.', 'info')
            return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html', title='Forgot Password')

# API routes
@app.route('/api/health')
def health_check():
    """API health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "timestamp": str(datetime.datetime.now())
    })

# Run the application
if __name__ == "__main__":
    app.run(debug=True)
