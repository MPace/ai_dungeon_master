"""
Authentication Service
"""
from flask import session
from app.models.user import User
from app.extensions import get_db, verify_password
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate a user with username and password"""
        db = get_db()
        if db is None:
            return None
        
        user = db.users.find_one({'username': username})
        
        if user is not None and verify_password(password, user.get('password_hash', '')):
            return user
        return None
    
    @staticmethod
    def update_last_login(user_id):
        """Update the last_login timestamp for a user"""
        db = get_db()
        if db is None:
            return False
        
        try:
            db.users.update_one(
                {'_id': user_id},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            return True
        except Exception as e:
            # Log the error but don't raise it to prevent breaking authentication flow
            import logging
            logging.error(f"Failed to update last_login: {e}")
            return False
        
    @staticmethod
    def register_user(username, email, password):
        """
        Register a new user
        
        Args:
            username (str): The username
            email (str): The email
            password (str): The plain text password
            
        Returns:
            dict: Result with success status and message/user
        """
        try:
            db = get_db()
            if db is None:
                logger.error("Database connection failed during registration")
                return {'success': False, 'error': 'Database connection error'}
            
            # Check if username already exists
            existing_user = db.users.find_one({'username': username})
            if existing_user:
                logger.warning(f"Registration attempt with existing username: {username}")
                return {'success': False, 'error': 'Username already exists'}
            
            # Check if email already exists
            existing_email = db.users.find_one({'email': email})
            if existing_email:
                logger.warning(f"Registration attempt with existing email: {email}")
                return {'success': False, 'error': 'Email already registered'}
            
            # Create new user
            password_hash = User.hash_password(password)
            
            user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )
            
            # Insert user into database
            result = db.users.insert_one(user.to_dict())
            
            if result.inserted_id:
                logger.info(f"User registered successfully: {username}")
                return {'success': True, 'user': user}
            else:
                logger.error(f"Failed to insert user into database: {username}")
                return {'success': False, 'error': 'Failed to create user account'}
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def login_user(username, password):
        """
        Authenticate a user
        
        Args:
            username (str): The username
            password (str): The plain text password
            
        Returns:
            dict: Result with success status and message/user
        """
        try:
            db = get_db()
            if db is None:
                logger.error("Database connection failed during login")
                return {'success': False, 'error': 'Database connection error'}
            
            # Find user by username
            user_data = db.users.find_one({'username': username})
            if not user_data:
                logger.warning(f"Login attempt with non-existent username: {username}")
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Create user instance
            user = User.from_dict(user_data)
            
            # Verify password
            if not User.verify_password(password, user.password_hash):
                logger.warning(f"Failed login attempt for user: {username}")
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Update last login
            db.users.update_one(
                {'_id': user_data['_id']},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            
            logger.info(f"User logged in successfully: {username}")
            
            # Set session data
            session['user_id'] = user.user_id
            session['username'] = user.username
            
            return {'success': True, 'user': user}
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def logout_user():
        """
        Log out the current user
        
        Returns:
            dict: Result with success status
        """
        try:
            # Clear the session
            session.clear()
            return {'success': True}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_current_user():
        """
        Get the currently logged in user
        
        Returns:
            User: The current user or None
        """
        try:
            user_id = session.get('user_id')
            if not user_id:
                return None
            
            db = get_db()
            if db is None:
                logger.error("Database connection failed when getting current user")
                return None
            
            user_data = db.users.find_one({'user_id': user_id})
            if not user_data:
                return None
            
            return User.from_dict(user_data)
            
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None