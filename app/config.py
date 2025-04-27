"""
Configuration settings for different environments
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Database
    MONGO_URI = os.environ.get('MONGO_URI', '')
    
    # AI Service
    AI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    AI_MODEL = os.environ.get('OPERNAI_MODEL', 'gpt-4o')
    
    # Modal API configuration
    MODAL_API_URL = os.environ.get('MODAL_API_URL')
    MODAL_API_TOKEN = os.environ.get('MODAL_API_TOKEN')

    # Embedding model configuration
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Qdrant configuration
    QDRANT_URL = os.environ.get('QDRANT_URL')
    QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY')
    QDRANT_COLLECTION_NAME = os.environ.get('QDRANT_COLLECTION_NAME', 'memory_vectors')
    QDRANT_VECTOR_SIZE = int(os.environ.get('QDRANT_VECTOR_SIZE', '768'))

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
