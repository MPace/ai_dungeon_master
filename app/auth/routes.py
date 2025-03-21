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
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('game.dashboard'))
    return render_template('index.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username is None or password is None or username == "" or password == "":
        flash('Username and password are required', 'error')
        return redirect(url_for('auth.index'))
    
    user = AuthService.authenticate_user(username, password)
    
    if user:
        # Clear any existing session and create a new one
        session.clear()
        
        # Set session data
        session['user_id'] = str(user.get('_id'))
        session['username'] = user.get('username')
        
        # Force session to be saved
        session.permanent = True
        session.modified = True
        
        # Update last_login in user record
        AuthService.update_last_login(user.get('_id'))

        logging.info(f"Session after login: {dict(session)}")
        
        flash('Login successful!', 'success')
        return redirect(url_for('game.user_dashboard'))
    
    flash('Invalid username or password', 'error')
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
    user = AuthService.register_user(username, email, password)
    
    if user:
        # Set up session
        session['user_id'] = str(user.get('_id'))
        session['username'] = username
        
        flash('Registration successful! Welcome to AI Dungeon Master.', 'success')
        return redirect(url_for('game.user_dashboard'))
    
    flash('Failed to create user account', 'error')
    return redirect(url_for('auth.index'))

@auth_bp.route('/logout')
def logout():
    """User logout endpoint"""
    AuthService.logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.index'))