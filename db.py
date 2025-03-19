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
    
    if MONGO_URI is None or MONGO_URI == "":
        print("WARNING: MongoDB URI not found in environment variables.")
        print("Database functionality will be disabled.")
        return False
    
    try:
        #import SSL module
        import ssl


        # Connect to MongoDB
        client = MongoClient(
            MONGO_URI,
            ssl_cert_reqs=ssl.CERT_NONE,
            serverSelectionTimeoutMS=5000
        )
        
        # Ping the database to verify connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        
        # Get the database
        db = client.ai_dungeon_master  # You can change this to your preferred database name
        
        # Initialize collections if they don't exist
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
            print("Created 'users' collection")
            
            # Add unique index on username
            db.users.create_index("username", unique=True)
            print("Added unique index on username")
        
        if 'characters' not in db.list_collection_names():
            db.create_collection('characters')
            print("Created 'characters' collection")
            
            # Add unique index on character_id and user_id
            db.characters.create_index([("character_id", 1), ("user_id", 1)], unique=True)
            print("Added unique index on character_id and user_id")
        
        # Add the new character_drafts collection for the multi-page architecture
        if 'character_drafts' not in db.list_collection_names():
            db.create_collection('character_drafts')
            print("Created 'character_drafts' collection")
            
            # Add unique index on character_id and user_id
            db.character_drafts.create_index([("character_id", 1), ("user_id", 1)], unique=True)
            print("Added unique index on character_id and user_id for drafts")
            
            # Add TTL index to automatically expire drafts after 30 days of inactivity
            db.character_drafts.create_index("lastUpdated", expireAfterSeconds=2592000)
            print("Added TTL index to 'character_drafts' collection")
        
        # Add submission log collection for deduplication
        if 'submission_log' not in db.list_collection_names():
            db.create_collection('submission_log')
            print("Created 'submission_log' collection")
            
            # Add unique index on submission_id
            db.submission_log.create_index("submission_id", unique=True)
            print("Added unique index on submission_id")
            
            # Add TTL index to automatically expire logs after 1 day
            db.submission_log.create_index("timestamp", expireAfterSeconds=86400)
            print("Added TTL index to submission_log collection")
        
        if 'campaigns' not in db.list_collection_names():
            db.create_collection('campaigns')
            print("Created 'campaigns' collection")
        
        if 'sessions' not in db.list_collection_names():
            db.create_collection('sessions')
            print("Created 'sessions' collection")
        
        print("Database collections initialized.")
        return True
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False
    

def save_character(character_data, user_id=None):
    """
    Save a character to the database
    
    Args:
        character_data (dict): Character data to save
        user_id (str, optional): User ID to associate with the character
        
    Returns:
        str: Character ID if successful, None otherwise
    """
    db = get_db()
    if db is None:
        print("Database not available, cannot save character")
        return None
    
    # If character doesn't have an ID, generate one
    if 'character_id' not in character_data:
        character_data['character_id'] = str(uuid.uuid4())
        print(f"Generated new character_id: {character_data['character_id']}")
    
    character_id = character_data['character_id']
    
    # Add metadata
    character_data['created_at'] = character_data.get('created_at', datetime.utcnow())
    character_data['updated_at'] = datetime.utcnow()
    character_data['last_played'] = datetime.utcnow()  # Initialize last_played
    character_data['user_id'] = user_id
    
    try:
        # First, check if this was a draft and delete it from the drafts collection
        if 'isDraft' in character_data and character_data['isDraft'] is False:
            print(f"Completed character (was draft): {character_id}")
            
            # Delete from character_drafts
            try:
                draft_result = db.character_drafts.delete_one({
                    'character_id': character_id,
                    'user_id': user_id
                })
                print(f"Deleted {draft_result.deleted_count} draft entries")
            except Exception as draft_error:
                print(f"Error deleting draft: {draft_error}")
        
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
            print(f"Character {character_data.get('name', 'Unknown')} updated successfully with upsert")
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
            print(f"Character {character_data.get('name', 'Unknown')} saved with ID: {character_id} using upsert")
            return character_id
    
    except Exception as e:
        print(f"Error saving character: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_db():
    """Get the database instance"""
    global db
    if db is None:
        if init_db() and client:
            # Explicitly specify the database name
            db = client.ai_dungeon_master
    return db

def close_db():
    """Close the database connection"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")