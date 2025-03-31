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
        Authenticate a user and create a secure session
        
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
                
                # Add a small delay to prevent timing attacks
                import time
                time.sleep(0.5)  
                
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Create user instance
            user = User.from_dict(user_data)
            
            # Verify password
            if not User.verify_password(password, user.password_hash):
                logger.warning(f"Failed login attempt for user: {username}")
                
                # Track failed login attempts (could be expanded to implement lockout)
                db.users.update_one(
                    {'_id': user_data['_id']},
                    {'$inc': {'failed_login_attempts': 1}}
                )
                
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Reset failed login attempts counter
            db.users.update_one(
                {'_id': user_data['_id']},
                {'$set': {'failed_login_attempts': 0, 'last_login': datetime.utcnow()}}
            )
            
            logger.info(f"User logged in successfully: {username}")
            
            # Regenerate session to prevent session fixation attacks
            # Clear previous session and create a new one
            session.clear()
            
            # Set session data
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['login_time'] = datetime.utcnow().isoformat()
            
            # Mark session as modified to ensure it's saved
            session.permanent = True
            session.modified = True
            
            return {'success': True, 'user': user}
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def logout_user():
        """
        Log out the current user by properly clearing session data
        
        Returns:
            dict: Result with success status
        """
        try:
            # Get user info for logging before clearing session
            username = session.get('username', 'Unknown')
            
            # Clear the session completely
            session.clear()
            
            # Regenerate session id
            session.modified = True
            
            logger.info(f"User logged out successfully: {username}")
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
        
    @staticmethod
    def user_exists(username, email):
        """
        Check if a username or email already exists in the database
        
        Args:
            username (str): The username to check
            email (str): The email to check
            
        Returns:
            bool: True if the username or email exists, False otherwise
        """
        try:
            db = get_db()
            if db is None:
                logger.error("Database connection failed when checking user existence")
                return False
            
            # Check if username exists
            username_exists = db.users.find_one({'username': username}) is not None
            
            # Check if email exists
            email_exists = db.users.find_one({'email': email}) is not None
            
            return username_exists or email_exists
            
        except Exception as e:
            logger.error(f"Error checking user existence: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Return False on error to avoid blocking registration
            # (though the error will likely cause other issues)
            return False