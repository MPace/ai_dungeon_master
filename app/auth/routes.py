"""
Auth routes
"""
from flask import render_template, request, redirect, url_for, flash, session
from app.auth import auth_bp
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

@auth_bp.route('/')
def index():
    """Landing page with login form"""
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('characters.dashboard'))
    return render_template('index.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    logger.info("=============================================")
    logger.info(f"Login attempt for user: {username}")
    
    if username is None or password is None or username == "" or password == "":
        logger.error("Missing username or password")
        flash('Username and password are required', 'error')
        return redirect(url_for('auth.index'))
    
    # Use AuthService to authenticate user
    result = AuthService.login_user(username, password)
    
    if result['success']:
        flash('Login successful!', 'success')
        logger.info(f"Redirecting to dashboard for user '{username}'...")
        return redirect(url_for('characters.dashboard'))
    else:
        flash(result.get('error', 'Invalid username or password'), 'error')
        return redirect(url_for('auth.index'))

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    print("============ REGISTRATION ATTEMPT ============")
    print(f"Attempting to register username: {username}, email: {email}")
    
    # Validate inputs
    if not username or not password or not email:
        print("Missing required fields")
        flash('All fields are required', 'error')
        return redirect(url_for('auth.index'))
    
    # Validate username format (alphanumeric, no spaces)
    if not username.isalnum():
        print("Username not alphanumeric")
        flash('Username must contain only letters and numbers', 'error')
        return redirect(url_for('auth.index'))
    
    # Validate password strength (at least 8 characters)
    if len(password) < 8:
        print("Password too short")
        flash('Password must be at least 8 characters long', 'error')
        return redirect(url_for('auth.index'))
    
    # Use AuthService to register user
    result = AuthService.register_user(username, email, password)
    
    if result['success']:
        # Automatically log in the user after registration
        login_result = AuthService.login_user(username, password)
        if login_result['success']:
            flash('Registration successful! Welcome to AI Dungeon Master.', 'success')
            return redirect(url_for('characters.dashboard'))
        else:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.index'))
    else:
        flash(result.get('error', 'Registration failed'), 'error')
        return redirect(url_for('auth.index'))

@auth_bp.route('/logout')
def logout():
    """User logout endpoint"""
    AuthService.logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.index'))