"""
Game Service
"""
from app.models.game_session import GameSession
from app.services.ai_service import AIService
from app.services.character_service import CharacterService
from app.extensions import get_db
from datetime import datetime
import uuid
import logging
import random

logger = logging.getLogger(__name__)

class GameService:
    """Service for handling game session operations"""
    
    @staticmethod
    def create_session(character_id, user_id):
        """
        Create a new game session
        
        Args:
            character_id (str): Character ID
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and session
        """
        try:
            # Get character data to verify ownership
            character = CharacterService.get_character(character_id, user_id)
            if character is None:
                logger.error(f"Character not found for session creation: {character_id}")
                return {'success': False, 'error': 'Character not found'}
            
            # Create a new session object
            session_id = str(uuid.uuid4())
            
            # Create a new GameSession object
            game_session = GameSession(
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                game_state='intro',
                history=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save session to database
            db = get_db()
            if db is None:
                logger.error("Database connection failed when creating session")
                return {'success': False, 'error': 'Database connection error'}
            
            # Convert GameSession to dictionary for storage
            session_dict = game_session.to_dict()
            
            # Insert into database
            result = db.sessions.insert_one(session_dict)
            
            if result.inserted_id:
                logger.info(f"Game session created: {session_id}")
                
                # Update character's last_played timestamp
                db.characters.update_one(
                    {'character_id': character_id},
                    {'$set': {'last_played': datetime.utcnow()}}
                )
                
                return {'success': True, 'session': game_session}
            else:
                logger.error(f"Failed to create game session")
                return {'success': False, 'error': 'Failed to create game session'}
                
        except Exception as e:
            logger.error(f"Error creating game session: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_session(session_id, user_id=None):
        """
        Get a game session by ID
        
        Args:
            session_id (str): Session ID
            user_id (str, optional): User ID for permission check
            
        Returns:
            dict: Result with success status and session
        """
        try:
            db = get_db()
            if db is None:
                logger.error("Database connection failed when getting session")
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {'session_id': session_id}
            if user_id:
                query['user_id'] = user_id
            
            # Find session
            session_data = db.sessions.find_one(query)
            
            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return {'success': False, 'error': 'Session not found'}
            
            session = GameSession.from_dict(session_data)
            return {'success': True, 'session': session}
            
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def send_message(session_id, message, user_id):
        """
        Send a message in a game session
        
        Args:
            session_id (str): Session ID
            message (str): User message
            user_id (str): User ID
            
        Returns:
            dict: Result with success status and AI response
        """
        try:
            # Check if we have a session ID
            if session_id is not None:
                # Try to get existing session
                session_result = GameService.get_session(session_id, user_id)
                if not session_result['success']:
                    logger.warning(f"Existing session not found: {session_id}, creating new session")
                    # We'll continue below to create a new session
                else:
                    session = session_result['session']
                    # Add user message to session history
                    session.add_message('player', message)
                    
                    # Proceed with existing session processing
                    return GameService._process_message(session, message, user_id)
            
            # If we get here, we need to create a new session
            # Check if we have character_id in the message or character_data
            character_id = None
            
            # Try to extract character_id from message if it's in JSON format
            if isinstance(message, dict) and 'character_id' in message:
                character_id = message.get('character_id')
            # Or if it was properly sent in character_data
            elif isinstance(message, str) and hasattr(message, 'character_data'):
                character_id = message.character_data.get('character_id')
            
            # Try to get the character_id from character_data
            character_id = None
            
            # Get the first character for this user
            characters = CharacterService.list_characters(user_id)
            if characters and len(characters) > 0:
                character_id = characters[0].character_id
                logger.info(f"Using first character: {character_id}")
            else:
                return {'success': False, 'error': "No characters found for this user"}
            
            # Create a new session with the character_id
            session_result = GameService.create_session(character_id, user_id)
            if not session_result['success']:
                return session_result
            
            session = session_result['session']
            
            # Add user message to session history
            session.add_message('player', message)
            
            # Process the message
            return GameService._process_message(session, message, user_id)
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _process_message(session, message, user_id):
        """Helper method to process a message in an existing session"""
        try:
            # Get character data
            character = CharacterService.get_character(session.character_id, user_id)
            if character is None:
                logger.error(f"Character not found: {session.character_id}")
                return {'success': False, 'error': 'Character not found'}
            
            # Call AI service to generate response
            ai_service = AIService()
            ai_response = ai_service.generate_response(
                message, 
                session.history, 
                character.to_dict(), 
                session.game_state
            )
            
            # Add AI response to session history
            session.add_message('dm', ai_response.response_text)
            
            # Update game state based on message content (simplified)
            GameService._update_game_state(session, message)
            
            # Save updated session
            db = get_db()
            if db is None:
                logger.error("Database connection failed when saving session")
                return {'success': False, 'error': 'Database connection error'}
            
            result = db.sessions.update_one(
                {'session_id': session.session_id},
                {'$set': session.to_dict()}
            )
            
            if result.acknowledged:
                logger.info(f"Session updated: {session.session_id}")
                
                # Update character's last_played timestamp
                db.characters.update_one(
                    {'character_id': session.character_id},
                    {'$set': {'last_played': datetime.utcnow()}}
                )
                
                return {
                    'success': True, 
                    'response': ai_response.response_text,
                    'session_id': session.session_id,
                    'game_state': session.game_state
                }
            else:
                logger.error(f"Failed to update session: {session.session_id}")
                return {'success': False, 'error': 'Failed to update session'}
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}

    @staticmethod
    def roll_dice(dice_type, modifier=0):
        """
        Roll a die
        
        Args:
            dice_type (str): Type of die to roll (e.g., 'd20')
            modifier (int): Modifier to add to roll
            
        Returns:
            dict: Roll result
        """
        try:
            # Parse the dice type (e.g., "d20" -> 20)
            sides = int(dice_type[1:])
            
            if sides <= 0:
                return {'success': False, 'error': 'Invalid dice type'}
            
            # Roll the dice
            result = random.randint(1, sides)
            modified_result = result + modifier
            
            return {
                'success': True,
                'dice': dice_type,
                'result': result,
                'modifier': modifier,
                'modified_result': modified_result
            }
            
        except Exception as e:
            logger.error(f"Error rolling dice: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _update_game_state(session, message):
        """
        Update game state based on message content
        
        Args:
            session (GameSession): Game session
            message (str): User message
            
        Returns:
            None
        """
        old_state = session.game_state
        
        # Simple keyword-based state update
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['attack', 'fight', 'hit', 'cast']):
            session.game_state = 'combat'
        elif any(word in message_lower for word in ['talk', 'speak', 'ask', 'say']):
            session.game_state = 'social'
        elif any(word in message_lower for word in ['look', 'search', 'investigate', 'explore']):
            session.game_state = 'exploration'
        
        if old_state != session.game_state:
            logger.info(f"Game state changed from {old_state} to {session.game_state}")