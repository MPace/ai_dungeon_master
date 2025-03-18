import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment variable
MONGO_URI = os.getenv("MONGO_URI")

# Initialize the client
client = None
db = None

def init_db():
    """Initialize the database connection"""
    global client, db
    
    if not MONGO_URI:
        print("WARNING: MongoDB URI not found in environment variables.")
        print("Database functionality will be disabled.")
        return False
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        
        # Ping the database to verify connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        
        # Get the database
        db = client.ai_dungeon_master  # You can change this to your preferred database name
        
        # Initialize collections if they don't exist
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
        
        if 'characters' not in db.list_collection_names():
            db.create_collection('characters')
        
        if 'campaigns' not in db.list_collection_names():
            db.create_collection('campaigns')
        
        if 'sessions' not in db.list_collection_names():
            db.create_collection('sessions')
        
        print("Database collections initialized.")
        return True
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return False

def get_db():
    """Get the database instance"""
    global db
    if db is None:
        init_db()
    return db

def close_db():
    """Close the database connection"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")