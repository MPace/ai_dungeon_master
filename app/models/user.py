"""
User model
"""
from datetime import datetime
import bcrypt
import hashlib
import uuid
from bson.objectid import ObjectId

class User:
    """User model for authentication and profile information"""
    
    def __init__(self, username, email, password_hash=None, user_id=None, 
                 created_at=None, last_login=None, _id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.user_id = user_id or str(uuid.uuid4())
        self.created_at = created_at or datetime.utcnow()
        self.last_login = last_login
        self._id = _id
    
    @classmethod
    def from_dict(cls, data):
        """Create a User instance from a dictionary"""
        if not data:
            return None
        
        # Convert _id from ObjectId to string if present
        _id = data.get('_id')
        if isinstance(_id, ObjectId):
            _id = str(_id)
        
        return cls(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=data.get('password_hash'),
            user_id=data.get('user_id'),
            created_at=data.get('created_at'),
            last_login=data.get('last_login'),
            _id=_id
        )
    
    def to_dict(self):
        """Convert User instance to a dictionary"""
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'last_login': self.last_login,
            # Don't include _id as it's handled by MongoDB
        }
    
    @staticmethod
    def hash_password(password):
        """Hash a password with bcrypt"""
        try:
            # Generate a salt and hash the password
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            
            # Return the hash as a string
            return password_hash.decode('utf-8')
        except Exception as e:
            print(f"Error hashing password: {e}")
            # Fallback to a less secure method if bcrypt is unavailable
            return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against a stored hash"""
        try:
            # Check if this is a bcrypt hash
            if password_hash.startswith('$2'):
                # Bcrypt password check
                password_bytes = password.encode('utf-8')
                hash_bytes = password_hash.encode('utf-8')
                return bcrypt.checkpw(password_bytes, hash_bytes)
            else:
                # Fallback SHA-256 check for legacy passwords
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
        except Exception as e:
            print(f"Error verifying password: {e}")
            return False