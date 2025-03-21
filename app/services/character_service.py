"""
Character Service
"""
from app.models.character import Character
from app.extensions import get_db
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class CharacterService:
    """Service for handling character operations"""
    
    @staticmethod
    def create_character(character_data, user_id):
        """
        Create a new character
        
        Args:
            character_data (dict): Character data
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and message/character
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when creating character")
                return {'success': False, 'error': 'Database connection error'}
            
            # Add user_id to character data
            character_data['user_id'] = user_id
            
            # Generate character_id if not provided
            if 'character_id' not in character_data:
                character_data['character_id'] = str(uuid.uuid4())
            
            # Create character instance
            character = Character.from_dict(character_data)
            
            # Mark as complete (not a draft)
            character.is_draft = False
            character.completed_at = datetime.utcnow()
            
            # Save to database
            CharacterService._save_character(character)
            
            return {'success': True, 'character': character}
            
        except Exception as e:
            logger.error(f"Error creating character: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def save_character_draft(character_data, user_id):
        """
        Save a character draft
        
        Args:
            character_data (dict): Character data
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and message/character
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when saving character draft")
                return {'success': False, 'error': 'Database connection error'}
            
            # Add user_id to character data
            character_data['user_id'] = user_id
            
            # Generate character_id if not provided
            if 'character_id' not in character_data:
                character_data['character_id'] = str(uuid.uuid4())
            
            # Create character instance
            character = Character.from_dict(character_data)
            
            # Mark as draft
            character.is_draft = True
            
            # Save to database
            result = db.character_drafts.replace_one(
                {'character_id': character.character_id, 'user_id': user_id},
                {**character.to_dict(), 'lastUpdated': datetime.utcnow()},
                upsert=True
            )
            
            if result.acknowledged:
                logger.info(f"Character draft saved: {character.name}")
                return {'success': True, 'character': character}
            else:
                logger.error(f"Failed to save character draft: {character.name}")
                return {'success': False, 'error': 'Failed to save character draft'}
            
        except Exception as e:
            logger.error(f"Error saving character draft: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_character(character_id, user_id=None):
        """
        Get a character by ID
        
        Args:
            character_id (str): Character ID
            user_id (str, optional): User ID for permission check
            
        Returns:
            dict: Result with success status and character
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when getting character")
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {'character_id': character_id}
            if user_id:
                query['user_id'] = user_id
            
            # Try to find in main characters collection
            character_data = db.characters.find_one(query)
            
            # If not found, try drafts
            if not character_data:
                character_data = db.character_drafts.find_one(query)
            
            if not character_data:
                logger.warning(f"Character not found: {character_id}")
                return {'success': False, 'error': 'Character not found'}
            
            character = Character.from_dict(character_data)
            return {'success': True, 'character': character}
            
        except Exception as e:
            logger.error(f"Error getting character: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_characters(user_id):
        """
        List characters for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and characters list
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when listing characters")
                return {'success': False, 'error': 'Database connection error'}
            
            # Get characters that are not drafts
            characters_data = list(db.characters.find({
                'user_id': user_id,
                '$or': [
                    {'isDraft': False},
                    {'isDraft': {'$exists': False}}
                ]
            }).sort('last_played', -1))
            
            characters = [Character.from_dict(data) for data in characters_data]
            
            return {'success': True, 'characters': characters}
            
        except Exception as e:
            logger.error(f"Error listing characters: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def list_character_drafts(user_id):
        """
        List character drafts for a user
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and drafts list
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when listing character drafts")
                return {'success': False, 'error': 'Database connection error'}
            
            drafts_data = list(db.character_drafts.find({
                'user_id': user_id
            }).sort('lastUpdated', -1))
            
            drafts = [Character.from_dict(data) for data in drafts_data]
            
            return {'success': True, 'drafts': drafts}
            
        except Exception as e:
            logger.error(f"Error listing character drafts: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_character(character_id, user_id):
        """
        Delete a character
        
        Args:
            character_id (str): Character ID
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when deleting character")
                return {'success': False, 'error': 'Database connection error'}
            
            # Verify ownership
            character_data = db.characters.find_one({
                'character_id': character_id,
                'user_id': user_id
            })
            
            if not character_data:
                logger.warning(f"Character not found or access denied: {character_id}")
                return {'success': False, 'error': 'Character not found or access denied'}
            
            # Delete character
            result = db.characters.delete_one({
                'character_id': character_id,
                'user_id': user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Character deleted: {character_id}")
                
                # Also delete any drafts with this character_id
                db.character_drafts.delete_many({
                    'character_id': character_id,
                    'user_id': user_id
                })
                
                character_name = character_data.get('name', 'Unknown')
                return {'success': True, 'message': f"Character '{character_name}' deleted successfully"}
            else:
                logger.error(f"Failed to delete character: {character_id}")
                return {'success': False, 'error': 'Failed to delete character'}
            
        except Exception as e:
            logger.error(f"Error deleting character: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_character_draft(draft_id, user_id):
        """
        Delete a character draft
        
        Args:
            draft_id (str): Draft ID
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status
        """
        try:
            db = get_db()
            if not db:
                logger.error("Database connection failed when deleting character draft")
                return {'success': False, 'error': 'Database connection error'}
            
            # Verify ownership
            draft_data = db.character_drafts.find_one({
                'character_id': draft_id,
                'user_id': user_id
            })
            
            if not draft_data:
                logger.warning(f"Draft not found or access denied: {draft_id}")
                return {'success': False, 'error': 'Draft not found or access denied'}
            
            # Delete draft
            result = db.character_drafts.delete_one({
                'character_id': draft_id,
                'user_id': user_id
            })
            
            if result.deleted_count > 0:
                logger.info(f"Draft deleted: {draft_id}")
                
                draft_name = draft_data.get('name', 'Unnamed draft')
                return {'success': True, 'message': f"Draft '{draft_name}' deleted successfully"}
            else:
                logger.error(f"Failed to delete draft: {draft_id}")
                return {'success': False, 'error': 'Failed to delete draft'}
            
        except Exception as e:
            logger.error(f"Error deleting draft: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _save_character(character):
        """
        Internal method to save a character to the database
        
        Args:
            character (Character): Character to save
            
        Returns:
            bool: Success status
        """
        db = get_db()
        if not db:
            logger.error("Database connection failed when saving character")
            return False
        
        try:
            # First, check if this was a draft and delete it from the drafts collection
            if not character.is_draft:
                logger.info(f"Completed character (was draft): {character.character_id}")
                draft_result = db.character_drafts.delete_one({
                    'character_id': character.character_id,
                    'user_id': character.user_id
                })
                logger.info(f"Deleted {draft_result.deleted_count} draft entries")
            
            # Update character data
            character.updated_at = datetime.utcnow()
            if not character.created_at:
                character.created_at = character.updated_at
            
            # Check if character already exists
            existing_character = db.characters.find_one({
                'character_id': character.character_id
            })
            
            if existing_character:
                # Update existing character
                result = db.characters.update_one(
                    {'character_id': character.character_id},
                    {'$set': character.to_dict()}
                )
                
                if result.modified_count > 0:
                    logger.info(f"Character updated: {character.name}")
                else:
                    logger.info(f"No changes to character: {character.name}")
                
                return True
            else:
                # Insert new character
                result = db.characters.insert_one(character.to_dict())
                
                if result.inserted_id:
                    logger.info(f"Character created: {character.name}")
                    return True
                else:
                    logger.error(f"Failed to insert character: {character.name}")
                    return False
                
        except Exception as e:
            logger.error(f"Error saving character: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False