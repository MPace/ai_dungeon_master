"""
Configuration settings for different environments
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Security
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # Controls cross-site request behavior
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)  # Session expires after 1 day
    
    # Database
    MONGO_URI = os.environ.get('MONGO_URI', '')
    
    # AI Service
    AI_API_KEY = os.environ.get('AI_API_KEY', '')
    AI_MODEL = os.environ.get('AI_MODEL', 'grok-1')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Application settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    # Use an in-memory database for testing
    MONGO_URI = os.environ.get('TEST_MONGO_URI', 'mongodb://localhost:27017/aidm_test')
    # Reduce session lifetime for testing
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)

class ProductionConfig(Config):
    """Production configuration"""
    # In production, SECRET_KEY should always be set from environment
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    
    # Security settings for production
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    
    # Set stricter SameSite policy in production
    SESSION_COOKIE_SAMESITE = 'Strict'