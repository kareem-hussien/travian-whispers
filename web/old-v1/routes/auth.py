# web/routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..utils.decorators import redirect_if_authenticated

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@redirect_if_authenticated
def login():
    """User login route."""
    if request.method == 'POST':
        # Login logic here
        pass
    return render_template('auth/login.html', title='Login')

@auth_bp.route('/register', methods=['GET', 'POST'])
@redirect_if_authenticated
def register():
    """User registration route."""
    if request.method == 'POST':
        # Registration logic here
        pass
    return render_template('auth/register.html', title='Register')

# Add other auth routes...