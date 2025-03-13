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
    return render_template('user/dashboard.html', title='Dashboard')

@app.route('/profile')
def profile():
    """User profile route."""
    if 'user_id' not in session:
        flash('Please log in to access your profile', 'warning')
        return redirect(url_for('login'))
    return render_template('user/profile.html', title='Profile')

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
