"""
Extensions module.
Each extension is initialized in the app factory located in app/__init__.py
"""
import pymongo
from flask import g, session, redirect, url_for, flash, request
from functools import wraps
import os
import logging
from datetime import datetime, timedelta
import uuid
import numpy as np
from dotenv import load_dotenv
from app.services.embedding_service import EmbeddingService

load_dotenv()

embedding_service = None

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
if not logger.handlers:  # Only configure if not already configured
    handler = logging.FileHandler('app.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

# Initialize MongoDB client
mongo_client = None
mongo_db = None
db = None
login_manager = None

# Login manager functionality (simplified version of Flask-Login)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Checking authentication for route: {request.path}")
        
        # Check if user is logged in
        if 'user_id' not in session:
            logger.error(f"AUTHENTICATION FAILED: No user_id in session for {request.path}")
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.index'))
        
        # Check session age to enforce re-login after extended periods
        # This is optional but recommended for sensitive operations
        if 'login_time' in session:
            try:
                login_time = datetime.fromisoformat(session['login_time'])
                max_age = timedelta(days=1)  # Adjust as needed
                
                if datetime.utcnow() - login_time > max_age:
                    logger.warning(f"Session expired for user: {session.get('username')}")
                    session.clear()
                    flash('Your session has expired. Please log in again.', 'warning')
                    return redirect(url_for('auth.index'))
            except (ValueError, TypeError) as e:
                logger.error(f"Error checking session age: {e}")
        
        # Authentication successful
        logger.info(f"Authentication successful for user: {session.get('username', 'Unknown')}")
        return f(*args, **kwargs)
    return decorated_function

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

logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f".env file exists: {os.path.exists('.env')}")
mongo_uri = os.getenv("MONGO_URI")
logger.info(f"MONGO_URI found: {'Yes' if mongo_uri else 'No'}")
if mongo_uri:
    logger.info(f"MONGO_URI starts with: {mongo_uri[:10]}...")

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

    # Add memory vectors collection
    if 'memory_vectors' not in db.list_collection_names():
        db.create_collection('memory_vectors')
        logger.info("Created 'memory_vectors' collection")
        
        try:
            # Create vector index for MongoDB 6.0+
            db.memory_vectors.create_index(
                [("embedding", "vector")],
                {
                    "name": "vector_index",
                    "vectorDimension": 768,  # Will match our embedding model dimension
                    "vectorDistanceMetric": "cosine"
                }
            )
            logger.info("Created vector index on 'embedding' field")
        except Exception as e:
            logger.warning(f"Could not create vector index (requires MongoDB 6.0+): {e}")
            logger.info("Will use fallback similarity calculations instead")
        
        # Create standard indexes
        db.memory_vectors.create_index([("session_id", 1), ("created_at", -1)])
        logger.info("Created index on 'session_id' and 'created_at'")
        
        db.memory_vectors.create_index([("character_id", 1), ("created_at", -1)])
        logger.info("Created index on 'character_id' and 'created_at'")
        
        db.memory_vectors.create_index([("memory_type", 1), ("created_at", -1)])
        logger.info("Created index on 'memory_type' and 'created_at'")
        
        # Create TTL index for short-term memories
        db.memory_vectors.create_index(
            [("created_at", 1)],
            expireAfterSeconds=7*24*60*60,  # 7 days in seconds
            partialFilterExpression={"memory_type": "short_term"}
        )
        logger.info("Created TTL index for 'short_term' memories")
    
    logger.info("Database collections initialized.")

# Authentication helper functions
def hash_password(password):
    """
    Hash a password with bcrypt for secure storage
    """
    try:
        # Import bcrypt here to avoid circular imports
        import bcrypt
        
        # Generate a salt and hash the password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        # Return the hash as a string
        return password_hash.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        # Fallback to a less secure method if bcrypt is unavailable
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """
    Verify a password against a stored hash
    """
    try:
        # Import bcrypt here to avoid circular imports
        import bcrypt
        
        # Check if this is a bcrypt hash
        if password_hash.startswith('$2'):
            # Bcrypt password check
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        else:
            # Fallback SHA-256 check for legacy passwords
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

# Add character management functions as needed
def save_character(character_data, user_id=None):
    """Save a character to the database"""
    db = get_db()
    if db is None:
        logger.error("Database not available, cannot save character")
        return None
    
    # If character doesn't have an ID, generate one
    if 'character_id' not in character_data:
        character_data['character_id'] = str(uuid.uuid4())
        logger.info(f"Generated new character_id: {character_data['character_id']}")
    
    character_id = character_data['character_id']
    
    # Add metadata
    character_data['created_at'] = character_data.get('created_at', datetime.utcnow())
    character_data['updated_at'] = datetime.utcnow()
    character_data['last_played'] = datetime.utcnow()  # Initialize last_played
    character_data['user_id'] = user_id
    
    try:
        # First, check if this was a draft and delete it from the drafts collection
        if 'isDraft' in character_data and character_data['isDraft'] is False:
            logger.info(f"Completed character (was draft): {character_id}")
            
            # Delete from character_drafts
            try:
                draft_result = db.character_drafts.delete_one({
                    'character_id': character_id,
                    'user_id': user_id
                })
                logger.info(f"Deleted {draft_result.deleted_count} draft entries")
            except Exception as draft_error:
                logger.error(f"Error deleting draft: {draft_error}")
        
        # Check if character already exists in characters collection
        existing_character = db.characters.find_one({
            'character_id': character_id,
            'user_id': user_id
        })
        
        if existing_character is not None:
            # Update existing character using replace_one for complete replacement
            result = db.characters.replace_one(
                {
                    'character_id': character_id,
                    'user_id': user_id
                },
                character_data,
                upsert=True  # Create if not exists
            )
            logger.info(f"Character {character_data.get('name', 'Unknown')} updated successfully with upsert")
            return character_id
        else:
            # Insert new character with upsert to prevent duplicates
            result = db.characters.update_one(
                {
                    'character_id': character_id,
                    'user_id': user_id
                },
                {'$set': character_data},
                upsert=True
            )
            logger.info(f"Character {character_data.get('name', 'Unknown')} saved with ID: {character_id} using upsert")
            return character_id
    
    except Exception as e:
        logger.error(f"Error saving character: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_character(character_id, user_id=None):
    """Get a character from the database"""
    db = get_db()
    if db is None:
        logger.error("Database not available, cannot get character")
        return None
    
    try:
        query = {'character_id': character_id}
        if user_id:
            query['user_id'] = user_id
            
        character = db.characters.find_one(query)
        
        if character:
            # Convert ObjectId to string for JSON serialization
            character['_id'] = str(character['_id'])
            return character
        
        return None
    except Exception as e:
        logger.error(f"Error getting character: {e}")
        return None

def delete_character(character_id, user_id=None):
    """Delete a character from the database"""
    db = get_db()
    if db is None:
        logger.error("Database not available, cannot delete character")
        return False
    
    try:
        query = {'character_id': character_id}
        if user_id:
            query['user_id'] = user_id
            
        result = db.characters.delete_one(query)
        
        if result.deleted_count > 0:
            logger.info(f"Character {character_id} deleted successfully")
            return True
        
        logger.warning(f"Character {character_id} not found for deletion")
        return False
    except Exception as e:
        logger.error(f"Error deleting character: {e}")
        return False

def init_extensions(app):
    """Initialize extensions"""
    global db, mongo_db, embedding_service
    # Initialize database
    with app.app_context():
        init_db()
        db = mongo_db
    
    # Initialize embedding service
    try:
        embedding_service = EmbeddingService()
        logger.info("Embedding service initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing embedding service: {e}")
        logger.warning("Application will run without embedding capabilities")
        embedding_service = None

    # Register close_db to be called when a request ends
    app.teardown_appcontext(close_db)
    
# Get the embedding service
def get_embedding_service():
    """Get the embedding service"""
    global embedding_service
    return embedding_service