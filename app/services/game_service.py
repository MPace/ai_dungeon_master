"""
Game Service
"""
import logging
from datetime import datetime, timedelta
import uuid
import random
from typing import Dict, Any, Optional, List

from app.services.character_service import CharacterService
from app.services.ai_service import AIService
from app.langgraph_core import get_orchestration_service
from app.extensions import get_db
from app.models.game_session import GameSession
from app.models.ai_response import AIResponse

logger = logging.getLogger(__name__)

class GameService:
    """Service for managing game sessions and orchestrating gameplay"""
    
    @staticmethod
    def create_session(character_id: str, user_id: str, 
                     world_id: Optional[str] = None, 
                     campaign_module_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new game session for a character
        
        Args:
            character_id: Character ID
            user_id: User ID
            world_id: Optional world identifier
            campaign_module_id: Optional campaign module identifier
            
        Returns:
            Dict containing session creation result
        """
        db = get_db()
        if db is None:
            logger.error("Database not available")
            return {
                'success': False,
                'error': 'Database not available'
            }
        
        try:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            
            # Create initial tracked narrative state
            initial_tracked_state = {
                'quest_status': {},
                'npc_dispositions': {},
                'location_states': {},
                'global_flags': [],
                'environment_state': {
                    'current_datetime': datetime.utcnow().isoformat(),
                    'current_day_phase': 'Morning',
                    'area_flags': {}
                }
            }
            
            # Create game session object
            game_session = GameSession(
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                world_id=world_id,
                campaign_module_id=campaign_module_id,
                game_state='intro',
                tracked_narrative_state=initial_tracked_state
            )
            
            # Save to database
            result = db.sessions.insert_one(game_session.to_dict())
            
            if result.inserted_id:
                logger.info(f"Created new game session: {session_id}")
                return {
                    'success': True,
                    'session': game_session,
                    'session_id': session_id
                }
            else:
                logger.error("Failed to insert game session into database")
                return {
                    'success': False,
                    'error': 'Failed to create game session'
                }
                
        except Exception as e:
            logger.error(f"Error creating game session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_session(session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a game session
        
        Args:
            session_id: Session ID
            user_id: Optional user ID for verification
            
        Returns:
            Dict containing session data or error
        """
        db = get_db()
        if db is None:
            logger.error("Database not available")
            return {
                'success': False,
                'error': 'Database not available'
            }
        
        try:
            # Build query
            query = {'session_id': session_id}
            if user_id:
                query['user_id'] = user_id
            
            # Get session from database
            session_doc = db.sessions.find_one(query)
            
            if session_doc:
                game_session = GameSession.from_dict(session_doc)
                return {
                    'success': True,
                    'session': game_session
                }
            else:
                logger.warning(f"Session not found: {session_id}")
                return {
                    'success': False,
                    'error': 'Session not found'
                }
                
        except Exception as e:
            logger.error(f"Error getting game session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def process_player_message(message: str, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process a player message using the LangGraph orchestration
        
        Args:
            message: Player's message
            session_id: Game session ID
            user_id: User ID
            
        Returns:
            Dict containing the result
        """
        if not message or not session_id or not user_id:
            return {
                'success': False,
                'error': 'Missing required parameters'
            }
        
        db = get_db()
        if db is None:
            logger.error("Database not available")
            return {
                'success': False,
                'error': 'Database not available'
            }
        
        try:
            # Get session to verify it exists and belongs to user
            session_result = GameService.get_session(session_id, user_id)
            
            if not session_result['success']:
                return session_result
            
            session = session_result['session']
            
            # Get the LangGraph orchestration service
            orchestration_service = get_orchestration_service()
            
            # Process the message through LangGraph
            logger.info(f"Processing message for session {session_id} through LangGraph")
            
            result = orchestration_service.process_message(
                session_id=session_id,
                message=message,
                character_id=session.character_id,
                user_id=user_id,
                world_id=session.world_id,
                campaign_module_id=session.campaign_module_id
            )
            
            if not result.get('success', False):
                logger.error(f"LangGraph processing failed: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to process message')
                }
            
            # Extract the DM response
            dm_response = result.get('response', '')
            
            # Create AI response object
            ai_response = AIResponse(
                response_text=dm_response,
                session_id=session_id,
                character_id=session.character_id,
                user_id=user_id,
                prompt=message
            )
            
            # Save the response to database
            response_dict = ai_response.to_dict()
            db.ai_responses.insert_one(response_dict)
            
            # Update session history
            session.add_message('player', message)
            session.add_message('dm', dm_response)
            
            # Update the session in database
            db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {
                    'history': session.history,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            logger.info(f"Successfully processed message for session {session_id}")
            
            return {
                'success': True,
                'response': dm_response,
                'session_id': session_id,
                'state': result.get('state', {})  # Include state for debugging
            }
            
        except Exception as e:
            logger.error(f"Error processing player message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_session_history(session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the conversation history for a session
        
        Args:
            session_id: Session ID
            user_id: Optional user ID for verification
            
        Returns:
            Dict containing history or error
        """
        result = GameService.get_session(session_id, user_id)
        
        if result['success']:
            session = result['session']
            return {
                'success': True,
                'history': session.history
            }
        else:
            return result
    
    @staticmethod
    def roll_dice(dice_type: str = 'd20', modifier: int = 0, 
                 user_id: Optional[str] = None, 
                 session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Roll dice and return the result
        
        Args:
            dice_type: Type of dice (e.g., 'd20', 'd6')
            modifier: Modifier to add to the roll
            user_id: User ID for logging
            session_id: Session ID for logging
            
        Returns:
            Dict containing roll result
        """
        try:
            # Extract dice number from type (e.g., 'd20' -> 20)
            dice_value = int(dice_type.lower().replace('d', ''))
            
            # Roll the dice
            roll = random.randint(1, dice_value)
            total = roll + modifier
            
            # Format result
            result = {
                'success': True,
                'dice': dice_type,
                'roll': roll,
                'modifier': modifier,
                'total': total,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Log the roll if we have session info
            if session_id and user_id:
                db = get_db()
                if db is not None:
                    db.dice_rolls.insert_one({
                        'session_id': session_id,
                        'user_id': user_id,
                        'dice_type': dice_type,
                        'roll': roll,
                        'modifier': modifier,
                        'total': total,
                        'timestamp': datetime.utcnow()
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error rolling dice: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_game_state(session_id: str, new_state: str) -> Dict[str, Any]:
        """
        Update the game state for a session
        
        Args:
            session_id: Session ID
            new_state: New game state
            
        Returns:
            Dict containing result
        """
        db = get_db()
        if db is None:
            logger.error("Database not available")
            return {
                'success': False,
                'error': 'Database not available'
            }
        
        try:
            # Update the game state
            result = db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {
                    'game_state': new_state,
                    'updated_at': datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated game state for session {session_id} to {new_state}")
                return {
                    'success': True,
                    'message': f'Game state updated to {new_state}'
                }
            else:
                logger.warning(f"No session found to update: {session_id}")
                return {
                    'success': False,
                    'error': 'Session not found'
                }
                
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
            return {
                'success': False,
                'error': str(e)
            }