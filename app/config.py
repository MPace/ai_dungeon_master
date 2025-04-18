"""
Configuration settings for different environments
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Database
    MONGO_URI = os.environ.get('MONGO_URI', '')
    
    # AI Service
    AI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    AI_MODEL = os.environ.get('OPERNAI_MODEL', 'gpt-4o')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Application settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'

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
    
    # Set stricter SameSite policy in production
    SESSION_COOKIE_SAMESITE = 'Strict'

    # Ensure cookies are only sent over HTTPS in production
    SESSION_COOKIE_SECURE = True
    SESSION_TYPE = 'redis'
    SESSION_USE_SIGNER = True

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'UTC'
