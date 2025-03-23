"""
Auth routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth import auth_bp
from app.services.auth_service import AuthService
from app.extensions import db
import logging


logger = logging.getLogger(__name__)

@auth_bp.route('/')
def index():
    """Landing page with login form"""
    logger.info('Auth index accessed')
    if 'user_id' in session:
        logger.info(f"User already logging, redirecting to dashboard. Session {session}")
        return redirect(url_for('game.dashboard'))
    return render_template('index.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    logger.info('Login endpoint accessed')
    username = request.form.get('username')
    password = request.form.get('password')
    
    logger.info(f"Login attempt for user: {username}")
    logger.debug(f"Request form data: {request.form}")

    if username is None or password is None or username == "" or password == "":
        flash('Username and password are required', 'error')
        return redirect(url_for('auth.index'))
    
    result = AuthService.login_user(username, password)
    
    if result['success']:
        logger.info(f"Login successful for user: {username}")
        logger.debug(f"Session after login: {session}")
        flash('Login successful!', 'success')
        session.modified = True

        try:
            redirect_url = url_for('game.dashboard')
            return redirect(redirect_url)
        except Exception as e:
            logger.error(f"Error during redirect: {str(e)}")
            flash(f"Internal server error during login: {str(e)}", 'error')
            return redirect(url_for('auth.index'))
        
    logger.warning(f"Login failed for user {username}: {result.get('error')}")
    flash(result.get('error', 'Invalid username or password'), 'error')
    return redirect(url_for('auth.index'))
    

@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    # Validate inputs
    if not username or not password or not email:
        flash('All fields are required', 'error')
        return redirect(url_for('auth.index'))
    
    # Validate username format (alphanumeric, no spaces)
    if not username.isalnum():
        flash('Username must contain only letters and numbers', 'error')
        return redirect(url_for('auth.index'))
    
    # Validate password strength (at least 8 characters)
    if len(password) < 8:
        flash('Password must be at least 8 characters long', 'error')
        return redirect(url_for('auth.index'))
    
    # Check if username or email already exists
    if AuthService.user_exists(username, email):
        flash('Username or email already exists', 'error')
        return redirect(url_for('auth.index'))
    
    # Register the user
    result = AuthService.register_user(username, email, password)
    
    if result['success']:
        # Log successful registration
        logger.info(f"User registered successfully: {username}")
        
        # Set up session
        user = result['user']
        session['user_id'] = user.user_id
        session['username'] = username
        session.modified = True
        
        flash('Registration successful! Welcome to AI Dungeon Master.', 'success')
        return redirect(url_for('game.dashboard'))
    
    logger.warning(f"Registration failed for {username}: {result.get('error')}")
    flash(result.get('error', 'Failed to create user account'), 'error')
    return redirect(url_for('auth.index'))

@auth_bp.route('/logout')
def logout():
    """User logout endpoint"""
    username = session.get('username', 'Unknown')
    logger.info(f"Logout initiated for user: {username}")
    
    result = AuthService.logout_user()
    
    if result['success']:
        logger.info(f"User {username} logged out successfully")
    else:
        logger.warning(f"Logout issue for {username}: {result.get('error')}")
        
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.index'))