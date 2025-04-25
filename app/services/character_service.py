"""
Character Service
"""
from app.models.character import Character
from datetime import datetime
import logging
import uuid
from flask import current_app, g

logger = logging.getLogger(__name__)

def get_db_for_service():
    """Get database connection for service"""
    try:
        # Try Flask application context first
        from flask import current_app, g
        
        # Check if we have a connection in the Flask app context
        if hasattr(g, 'db'):
            logger.debug("Using existing database connection from Flask context")
            return g.db
            
        # If we have a current_app, use it to get the MongoDB instance
        if current_app:
            logger.debug("Getting database connection from Flask app context")
            if 'mongodb' in current_app.extensions:
                return current_app.extensions['mongodb']
            # Fall back to check in extensions directly
            from app.extensions import mongo_db
            if mongo_db is not None:
                logger.debug("Using mongo_db from extensions module")
                return mongo_db
    except RuntimeError:
        # Working outside of Flask application context (e.g., in Celery worker)
        logger.debug("Working outside Flask context, using direct database connection")
    except Exception as e:
        logger.warning(f"Error accessing Flask context: {e}")
    
    try:
        # If we're outside Flask context, try to initialize a new connection
        import os
        import pymongo
        
        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            logger.error("MONGO_URI environment variable not set")
            return None
            
        logger.info("Creating new MongoDB connection outside Flask context")
        client = pymongo.MongoClient(
            mongo_uri,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        
        return client.ai_dungeon_master
            
    except Exception as e:
        logger.error(f"Error getting database connection: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

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
            db = get_db_for_service()
            if db is None:
                logger.error("Database connection failed when creating character")
                return {'success': False, 'error': 'Database connection error'}
            
            # Add user_id to character data if not already present
            if 'user_id' not in character_data:
                character_data['user_id'] = user_id
            
            # Generate character_id if not provided
            if 'character_id' not in character_data or not character_data['character_id']:
                character_data['character_id'] = str(uuid.uuid4())
                logger.info(f"Generated new character_id: {character_data['character_id']}")
            
            # Create character instance
            character = Character.from_dict(character_data)
            if character is None:
                logger.error(f"Failed to create Character from data: {character_data}")
                return {'success': False, 'error': 'Failed to create Character object'}
            
            # Mark as complete (not a draft)
            character.is_draft = False
            character.completed_at = datetime.utcnow()
            
            # Save to database directly
            character_dict = character.to_dict()
            
            # Insert or update in database
            result = db.characters.update_one(
                {'character_id': character.character_id, 'user_id': user_id},
                {'$set': character_dict},
                upsert=True
            )
            
            if result.acknowledged:
                logger.info(f"Character saved: {character.name} with ID: {character.character_id}")
                
                # Delete any drafts
                try:
                    db.character_drafts.delete_one({
                        'character_id': character.character_id,
                        'user_id': user_id
                    })
                    logger.info(f"Deleted draft for character: {character.character_id}")
                except Exception as draft_e:
                    logger.warning(f"Error deleting draft: {draft_e}")
                
                return {'success': True, 'character': character}
            else:
                logger.error(f"Failed to save character to database: {character.name}")
                return {'success': False, 'error': 'Failed to save character to database'}
                
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
            db = get_db_for_service()
            if db is None:
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
            db = get_db_for_service()
            if db is None:
                logger.error("Database connection failed when getting character")
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {'character_id': character_id}
            if user_id is not None:
                query['user_id'] = user_id
            
            logger.info(f"Querying for character with: {query}")
            
            # Find character
            character_data = db.characters.find_one(query)
            
            if not character_data:
                logger.warning(f"Character not found: {character_id}")
                return {'success': False, 'error': 'Character not found'}
            
            # Convert dictionary to Character object
            character = Character.from_dict(character_data)
            
            if character:
                logger.info(f"Character found: {character.name}")
                return {'success': True, 'character': character}
            else:
                logger.warning(f"Failed to create Character object from data: {character_id}")
                return {'success': False, 'error': 'Failed to create Character object'}
                    
        except Exception as e:
            logger.error(f"Error getting character: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
            db = get_db_for_service()
            if db is None:
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
            
            logger.info(f"Found {len(characters_data)} characters for user {user_id}")
            
            characters = []
            for data in characters_data:
                character = Character.from_dict(data)
                if character is not None:  # Only include valid characters
                    characters.append(character)
            
            logger.info(f"Converted {len(characters)} characters from database data")
            
            return {'success': True, 'characters': characters}
            
        except Exception as e:
            logger.error(f"Error listing characters: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
            db = get_db_for_service()
            if db is None:
                logger.error("Database connection failed when listing character drafts")
                return {'success': False, 'error': 'Database connection error'}
            
            drafts_data = list(db.character_drafts.find({
                'user_id': user_id
            }).sort('lastUpdated', -1))
            
            logger.info(f"Found {len(drafts_data)} drafts for user {user_id}")
            
            drafts = []
            for data in drafts_data:
                draft = Character.from_dict(data)
                if draft is not None:  # Only include valid drafts
                    drafts.append(draft)
            
            logger.info(f"Converted {len(drafts)} drafts from database data")
            
            return {'success': True, 'drafts': drafts}
            
        except Exception as e:
            logger.error(f"Error listing character drafts: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_character(character_id, user_id):
        """
        Delete a character and all associated memories
        
        Args:
            character_id (str): Character ID
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status
        """
        try:
            db = get_db_for_service()
            if db is None:
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
                
                # Delete character drafts
                db.character_drafts.delete_many({
                    'character_id': character_id,
                    'user_id': user_id
                })
                
                # Delete all associated memories
                memory_deletion = db.memory_vectors.delete_many({
                    'character_id': character_id
                })
                
                # Delete associated game sessions
                session_query = {'character_id': character_id}
                sessions = list(db.sessions.find(session_query, {'session_id': 1}))
                session_ids = [s['session_id'] for s in sessions]
                
                # Delete sessions
                if session_ids:
                    db.sessions.delete_many({'session_id': {'$in': session_ids}})
                    
                    # Delete session memories
                    db.memory_vectors.delete_many({'session_id': {'$in': session_ids}})
                    
                    logger.info(f"Deleted {len(session_ids)} sessions and their associated memories")
                
                character_name = character_data.get('name', 'Unknown')
                return {
                    'success': True, 
                    'message': f"Character '{character_name}' and all associated data deleted successfully",
                    'memories_deleted': memory_deletion.deleted_count
                }
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
            db = get_db_for_service()
            if db is None:
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
        db = get_db_for_service()
        if db is None:
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
    
    @staticmethod
    def check_submission(submission_id, user_id):
        """
        Check if a submission ID has already been processed
        to prevent duplicate submissions
        """
        db = get_db_for_service()
        if db is not None:
            try:
                # Look for this submission in the log
                return db.submission_log.find_one({
                    'submission_id': submission_id,
                    'user_id': user_id
                })
            except Exception as e:
                import logging
                logging.error(f"Error checking submission: {e}")
        return None
    
    @staticmethod
    def log_submission(submission_id, character_id, user_id):
        """
        Log a submission to prevent future duplicates
        """
        db = get_db_for_service()
        if db is not None:
            try:
                # Ensure the collection exists
                if 'submission_log' not in db.list_collection_names():
                    db.create_collection('submission_log')
                    # Add TTL index to auto-expire log entries after 1 day
                    db.submission_log.create_index("timestamp", expireAfterSeconds=86400)
                
                # Add the submission to the log
                db.submission_log.insert_one({
                    'submission_id': submission_id,
                    'character_id': character_id,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow()
                })
                return True
            except Exception as e:
                import logging
                logging.error(f"Error logging submission: {e}")
        return False
    
    @staticmethod
    def cleanup_orphaned_memories():
        """Periodically clean up orphaned memories with no corresponding character or session"""
        try:
            db = get_db_for_service()
            if db is None:
                logger.error("Database connection failed during memory cleanup")
                return {'success': False, 'error': 'Database connection error'}
            
            # Get all valid character IDs
            character_ids = set(doc['character_id'] for doc in db.characters.find({}, {'character_id': 1}))
            
            # Get all valid session IDs
            session_ids = set(doc['session_id'] for doc in db.sessions.find({}, {'session_id': 1}))
            
            # Find orphaned memories (excluding semantic memories which aren't tied to specific characters)
            orphaned_query = {
                '$and': [
                    {'memory_type': {'$ne': 'semantic'}},
                    {'$or': [
                        {'character_id': {'$nin': list(character_ids)}},
                        {'session_id': {'$nin': list(session_ids)}}
                    ]}
                ]
            }
            
            # Delete orphaned memories
            result = db.memory_vectors.delete_many(orphaned_query)
            
            logger.info(f"Cleaned up {result.deleted_count} orphaned memories")
            
            return {
                'success': True,
                'orphaned_memories_deleted': result.deleted_count
            }
        except Exception as e:
            logger.error(f"Error cleaning up orphaned memories: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
        
    @staticmethod
    def get_character_draft(draft_id, user_id):
        """
        Get a character draft by ID
        
        Args:
            draft_id (str): Draft ID
            user_id (str): User ID for permission check
            
        Returns:
            dict: Result with success status and character draft
        """
        try:
            db = get_db_for_service()
            if db is None:
                logger.error("Database connection failed when getting character draft")
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {'character_id': draft_id, 'user_id': user_id}
            
            logger.info(f"Querying for character draft with: {query}")
            
            # Find draft
            draft_data = db.character_drafts.find_one(query)
            
            if not draft_data:
                logger.warning(f"Character draft not found: {draft_id}")
                return {'success': False, 'error': 'Character draft not found'}
            
            # Convert dictionary to Character object
            draft = Character.from_dict(draft_data)
            
            if draft:
                logger.info(f"Character draft found: {draft.name if hasattr(draft, 'name') else 'Unnamed'}")
                return {'success': True, 'character': draft}
            else:
                logger.warning(f"Failed to create Character object from draft data: {draft_id}")
                return {'success': False, 'error': 'Failed to create Character object from draft data'}
                    
        except Exception as e:
            logger.error(f"Error getting character draft: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_world_info_for_characters(characters):
        """
        Enrich character objects with world and campaign information
        
        Args:
            characters (list): List of character objects
            
        Returns:
            list: Enriched character list
        """
        try:
            # World information will be loaded from YAML files
            worlds_dir = os.path.join(DATA_DIR, 'worlds')
            
            # Create a cache for worlds to avoid reading the same files multiple times
            world_cache = {}
            
            for character in characters:
                # Skip if character doesn't have worldId
                if not hasattr(character, 'worldId') or not character.worldId:
                    continue
                    
                world_id = character.worldId
                
                # Check if world is already in cache
                if world_id not in world_cache:
                    # Try to load world info from YAML file
                    world_file = os.path.join(worlds_dir, f"{world_id}.yaml")
                    if not os.path.exists(world_file):
                        world_file = os.path.join(worlds_dir, f"{world_id}.yml")
                    
                    if os.path.exists(world_file):
                        try:
                            with open(world_file, 'r', encoding='utf-8') as f:
                                world_data = yaml.safe_load(f)
                                world_cache[world_id] = world_data
                        except Exception as e:
                            logger.error(f"Error loading world file {world_file}: {e}")
                            world_cache[world_id] = None
                    else:
                        world_cache[world_id] = None
                
                # Add world info to character
                world_data = world_cache.get(world_id)
                if world_data:
                    character.worldName = world_data.get('name', 'Unknown World')
                    
                    # Add campaign info if available
                    if hasattr(character, 'campaignId') and character.campaignId:
                        campaign_id = character.campaignId
                        campaign_dir = os.path.join(DATA_DIR, 'campaigns', world_id)
                        
                        if os.path.exists(campaign_dir):
                            campaign_file = os.path.join(campaign_dir, f"{campaign_id}.yaml")
                            if not os.path.exists(campaign_file):
                                campaign_file = os.path.join(campaign_dir, f"{campaign_id}.yml")
                            
                            if os.path.exists(campaign_file):
                                try:
                                    with open(campaign_file, 'r', encoding='utf-8') as f:
                                        campaign_data = yaml.safe_load(f)
                                        character.campaignName = campaign_data.get('name', 'Unknown Campaign')
                                except Exception as e:
                                    logger.error(f"Error loading campaign file {campaign_file}: {e}")
            
            return characters
        except Exception as e:
            logger.error(f"Error enriching characters with world info: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return characters

    @staticmethod
    def format_date_for_display(date_value):
        """
        Format a date value for display
        
        Args:
            date_value: Date to format (datetime or string)
            
        Returns:
            str: Formatted date string
        """
        if date_value is None:
            return None
            
        try:
            # Convert string to datetime if necessary
            if isinstance(date_value, str):
                try:
                    date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except ValueError:
                    # If it's not a valid ISO format, return as is
                    return date_value
            
            # Format the datetime
            if isinstance(date_value, datetime):
                return date_value.strftime("%d/%m/%y %H:%M")
            
            # Return original value if we can't format it
            return date_value
        except Exception as e:
            logger.error(f"Error formatting date {date_value}: {e}")
            return date_value

    # Update the list_characters method to include world info
    @staticmethod
    def list_characters(user_id):
        """
        List characters for a user with enhanced information
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and characters list
        """
        try:
            db = get_db_for_service()
            if db is None:
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
            
            logger.info(f"Found {len(characters_data)} characters for user {user_id}")
            
            characters = []
            for data in characters_data:
                character = Character.from_dict(data)
                if character is not None:  # Only include valid characters
                    # Format last_played date for display
                    if hasattr(character, 'last_played') and character.last_played:
                        character.last_played_formatted = CharacterService.format_date_for_display(character.last_played)
                    
                    characters.append(character)
            
            logger.info(f"Converted {len(characters)} characters from database data")
            
            # Enrich characters with world and campaign info
            characters = CharacterService.get_world_info_for_characters(characters)
            
            return {'success': True, 'characters': characters}
            
        except Exception as e:
            logger.error(f"Error listing characters: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
