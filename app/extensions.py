"""
Extensions module.
Each extension is initialized in the app factory located in app/__init__.py
"""
import pymongo
from flask import g
import os
import logging

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MongoDB client
mongo_client = None
mongo_db = None

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = mongo_db
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    # MongoDB doesn't need explicit connection closing per request
    # But we keep this function for consistency and future proofing

def init_db():
    """Initialize the database connection"""
    global mongo_client, mongo_db
    
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        logger.warning("MongoDB URI not found in environment variables.")
        logger.warning("Database functionality will be disabled.")
        return False
    
    try:
        # Connect to MongoDB
        mongo_client = pymongo.MongoClient(
            mongo_uri,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        
        # Ping the database to verify connection
        mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
        
        # Get the database
        mongo_db = mongo_client.ai_dungeon_master
        
        # Initialize collections
        init_collections(mongo_db)
        
        return True
    
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def init_collections(db):
    """Initialize collections if they don't exist"""
    # Create collections if they don't exist
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
        logger.info("Created 'users' collection")
        
        # Add unique index on username
        db.users.create_index("username", unique=True)
        logger.info("Added unique index on username")
    
    if 'characters' not in db.list_collection_names():
        db.create_collection('characters')
        logger.info("Created 'characters' collection")
        
        # Add unique index on character_id and user_id
        db.characters.create_index([("character_id", 1), ("user_id", 1)], unique=True)
        logger.info("Added unique index on character_id and user_id")
    
    if 'character_drafts' not in db.list_collection_names():
        db.create_collection('character_drafts')
        logger.info("Created 'character_drafts' collection")
        
        # Add unique index on character_id and user_id
        db.character_drafts.create_index([("character_id", 1), ("user_id", 1)], unique=True)
        logger.info("Added unique index on character_id and user_id for drafts")
        
        # Add TTL index to automatically expire drafts after 30 days of inactivity
        db.character_drafts.create_index("lastUpdated", expireAfterSeconds=2592000)
        logger.info("Added TTL index to 'character_drafts' collection")
    
    if 'submission_log' not in db.list_collection_names():
        db.create_collection('submission_log')
        logger.info("Created 'submission_log' collection")
        
        # Add unique index on submission_id
        db.submission_log.create_index("submission_id", unique=True)
        logger.info("Added unique index on submission_id")
        
        # Add TTL index to automatically expire logs after 1 day
        db.submission_log.create_index("timestamp", expireAfterSeconds=86400)
        logger.info("Added TTL index to submission_log collection")
    
    if 'campaigns' not in db.list_collection_names():
        db.create_collection('campaigns')
        logger.info("Created 'campaigns' collection")
    
    if 'sessions' not in db.list_collection_names():
        db.create_collection('sessions')
        logger.info("Created 'sessions' collection")
    
    logger.info("Database collections initialized.")

def init_extensions(app):
    """Initialize extensions"""
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register close_db to be called when a request ends
    app.teardown_appcontext(close_db)