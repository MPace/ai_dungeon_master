from datetime import datetime
import uuid
from db import get_db

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
    else:
        print(f"Using existing character_id: {character_data['character_id']}")
    
    # Add metadata
    character_data['created_at'] = character_data.get('created_at', datetime.utcnow())
    character_data['updated_at'] = datetime.utcnow()
    character_data['last_played'] = datetime.utcnow()  # Initialize last_played
    character_data['user_id'] = user_id
    
    character_id = character_data['character_id']
    
    try:
        # First, check if this was a draft and delete it from the drafts collection
        if 'isDraft' in character_data and character_data['isDraft'] == False:
            print(f"Completed character (was draft): {character_id}")
            draft_result = db.character_drafts.delete_one({'character_id': character_id})
            print(f"Deleted {draft_result.deleted_count} draft entries")
        
        # Check if character already exists in characters collection
        existing_character = db.characters.find_one({'character_id': character_id})
        
        if existing_character:
            # Update existing character
            result = db.characters.update_one(
                {'character_id': character_id},
                {'$set': character_data}
            )
            if result.modified_count > 0:
                print(f"Character {character_data.get('name', 'Unknown')} updated successfully")
            else:
                print(f"No changes made to character {character_data.get('name', 'Unknown')}")
        else:
            # Insert new character
            result = db.characters.insert_one(character_data)
            if result.inserted_id:
                print(f"Character {character_data.get('name', 'Unknown')} saved with ID: {character_id}")
            else:
                print("Failed to save character")
                return None
        
        return character_id
    
    except Exception as e:
        print(f"Error saving character: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_character(character_id):
    """
    Retrieve a character from the database
    
    Args:
        character_id (str): Character ID to retrieve
        
    Returns:
        dict: Character data if found, None otherwise
    """
    db = get_db()
    if db is None:
        print("Database not available, cannot retrieve character")
        return None
    
    try:
        character = db.characters.find_one({'character_id': character_id})
        if character:
            # Convert ObjectId to string for JSON serialization
            character['_id'] = str(character['_id'])
            return character
        else:
            print(f"Character with ID {character_id} not found")
            return None
    
    except Exception as e:
        print(f"Error retrieving character: {e}")
        return None

def list_characters(user_id=None, limit=10):
    """
    List characters, optionally filtered by user ID
    
    Args:
        user_id (str, optional): User ID to filter by
        limit (int, optional): Maximum number of characters to return
        
    Returns:
        list: List of character data dictionaries
    """
    db = get_db()
    if db is None:
        print("Database not available, cannot list characters")
        return []
    
    try:
        # Create query, filter by user_id if provided
        query = {'user_id': user_id} if user_id else {}
        
        # Find characters, sort by updated_at
        cursor = db.characters.find(query).sort('updated_at', -1).limit(limit)
        
        # Convert cursor to list, serializing ObjectId
        characters = []
        for character in cursor:
            character['_id'] = str(character['_id'])
            characters.append(character)
        
        return characters
    
    except Exception as e:
        print(f"Error listing characters: {e}")
        return []

def delete_character(character_id):
    """
    Delete a character from the database
    
    Args:
        character_id (str): Character ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    db = get_db()
    if db is None:
        print("Database not available, cannot delete character")
        return False
    
    try:
        result = db.characters.delete_one({'character_id': character_id})
        if result.deleted_count > 0:
            print(f"Character with ID {character_id} deleted successfully")
            return True
        else:
            print(f"Character with ID {character_id} not found")
            return False
    
    except Exception as e:
        print(f"Error deleting character: {e}")
        return False