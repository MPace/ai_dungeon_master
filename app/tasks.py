"""
Celery tasks for AI Dungeon Master
"""
import logging
from celery import shared_task
from app.langgraph_core import get_orchestration_service
from app.extensions import get_db
from app.models.game_session import GameSession
from app.models.ai_response import AIResponse
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task(name='app.tasks.process_dm_message')
def process_dm_message(message, session_id, character_data, user_id):
    """
    Process a DM message asynchronously through LangGraph
    
    Args:
        message: Player's message
        session_id: Game session ID  
        character_data: Character information
        user_id: User ID
        
    Returns:
        dict: Processing result with DM response
    """
    try:
        logger.info(f"Starting async DM message processing for session {session_id}")
        
        # Get database connection
        db = get_db()
        if db is None:
            logger.error("Database not available in Celery task")
            return {
                'response': "I'm having trouble connecting to the game world. Please try again.",
                'error': 'Database connection failed',
                'success': False
            }
        
        # Get session information
        try:
            session_doc = db.sessions.find_one({'session_id': session_id})
            if not session_doc:
                logger.error(f"Session not found: {session_id}")
                return {
                    'response': "I couldn't find your game session. Please try starting a new game.",
                    'error': 'Session not found',
                    'success': False
                }
                
            game_session = GameSession.from_dict(session_doc)
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return {
                'response': "There was an error loading your game session.",
                'error': str(e),
                'success': False
            }
        
        # Get the LangGraph orchestration service
        try:
            orchestration_service = get_orchestration_service()
        except Exception as e:
            logger.error(f"Error getting orchestration service: {e}")
            return {
                'response': "The Dungeon Master is temporarily unavailable. Please try again.",
                'error': str(e),
                'success': False
            }
        
        # Process the message through LangGraph
        try:
            logger.info(f"Processing message through LangGraph for session {session_id}")
            
            result = orchestration_service.process_message(
                session_id=session_id,
                message=message,
                character_id=game_session.character_id,
                user_id=user_id,
                world_id=game_session.world_id,
                campaign_module_id=game_session.campaign_module_id
            )
            
            if not result.get('success', False):
                logger.error(f"LangGraph processing failed: {result.get('error')}")
                return {
                    'response': result.get('response', 'The Dungeon Master seems confused. Please try again.'),
                    'error': result.get('error', 'Processing failed'),
                    'success': False
                }
            
            # Extract the DM response
            dm_response = result.get('response', '')
            
            # Create and save AI response record
            try:
                ai_response = AIResponse(
                    response_text=dm_response,
                    session_id=session_id,
                    character_id=game_session.character_id,
                    user_id=user_id,
                    prompt=message
                )
                
                response_dict = ai_response.to_dict()
                db.ai_responses.insert_one(response_dict)
                
            except Exception as e:
                logger.error(f"Error saving AI response: {e}")
                # Continue anyway - the response was generated successfully
            
            # Update session history
            try:
                game_session.add_message('player', message)
                game_session.add_message('dm', dm_response)
                
                db.sessions.update_one(
                    {'session_id': session_id},
                    {'$set': {
                        'history': game_session.history,
                        'updated_at': datetime.utcnow()
                    }}
                )
                
            except Exception as e:
                logger.error(f"Error updating session history: {e}")
                # Continue anyway - the response was generated successfully
            
            logger.info(f"Successfully processed message for session {session_id}")
            
            return {
                'response': dm_response,
                'session_id': session_id,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error in LangGraph processing: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                'response': "The Dungeon Master encountered an unexpected error. Please try again.",
                'error': str(e),
                'success': False
            }
            
    except Exception as e:
        logger.error(f"Unhandled error in process_dm_message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'response': "An unexpected error occurred. Please try again.",
            'error': str(e),  
            'success': False
        }

@shared_task(name='app.tasks.test_task')
def test_task():
    """Simple test task to verify Celery is working"""
    logger.info("Test task executed successfully")
    return "Celery is working!"