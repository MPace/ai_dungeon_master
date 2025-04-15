"""
Celery tasks for AI Dungeon Master
"""
from app.celery_config import celery
import logging
from flask import current_app
from flask import Flask
from app.services.ai_service import AIService
from app.services.game_service import GameService

logger = logging.getLogger(__name__)
logger.info("Tasks module loading...")

def get_flask_app():
    from app import create_app
    return create_app()


@celery.task
def process_dm_message(message, session_id, character_data, user_id):
    """
    Process a message from a player to the AI Dungeon Master.
    This task runs asynchronously and returns the AI's response.
    
    Args:
        message (str): The player's message
        session_id (str): Current session ID or None for new session
        character_data (dict): Character data
        user_id (str): User ID
        
    Returns:
        dict: Response data containing AI's response and session info
    """
    logger.info(f"Processing DM message task for user {user_id}, session {session_id}")
    
    try:
    # Initialize services
        from app.services.ai_service import AIService
        from app.services.game_service import GameService
        
        ai_service = AIService()
        
        # Get or create a session
        if session_id:
            session_result = GameService.get_session(session_id, user_id)
            if session_result.get('success', False):
                session = session_result['session']
            else:
                # Create new session
                logger.warning(f"Session not found, creating new: {session_id}")
                session_result = GameService.create_session(character_data.get('character_id'), user_id)
                if not session_result.get('success', False):
                    return {
                        'success': False,
                        'error': session_result.get('error', 'Failed to create session')
                    }
                session = session_result['session']
        else:
            # Create new session
            logger.info(f"Creating new session for user {user_id}")
            session_result = GameService.create_session(character_data.get('character_id'), user_id)
            if not session_result.get('success', False):
                return {
                    'success': False,
                    'error': session_result.get('error', 'Failed to create session')
                }
            session = session_result['session']
        
        # Get character
        if hasattr(character_data, 'character_id'):
            character_id = character_data.character_id
        else:
            character_id = character_data.get('character_id')
        
        # Add player message to session
        session.add_message('player', message)
        
        # Generate AI response
        ai_response = ai_service.generate_response(
            message, 
            session.history, 
            character_data, 
            session.game_state
        )
        
        # Ensure valid response text
        response_text = "The Dungeon Master pauses, thinking about your request."
        if ai_response and hasattr(ai_response, 'response_text') and ai_response.response_text:
            response_text = ai_response.response_text
        
        # Add AI response to session
        session.add_message('dm', response_text)
        
        # Update game state based on content
        GameService._update_game_state(session, message, response_text)
        
        # Update session in database
        from app.extensions import get_db
        db = get_db()
        if db is not None:
            db.sessions.update_one(
                {'session_id': session.session_id},
                {'$set': session.to_dict()}
            )
        
        # Return result
        return {
            'success': True,
            'response': response_text,
            'session_id': session.session_id,
            'game_state': session.game_state
        }
    except Exception as e:
        logger.error(f"Error in process_dm_message task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a fallback response
        return {
            'success': True,  # Still return success to prevent frontend errors
            'response': f"The Dungeon Master seems momentarily distracted. (Error: {str(e)})",
            'session_id': session_id
        }
               

@celery.task(name='tasks.generate_memory_summary', bind=True)
def generate_memory_summary(self, session_id, user_id):
    """Generate a summary of memories for a session"""
    try:
        app = get_flask_app()
        with app.app_context():
            from app.services.summarization_service import SummarizationService
        
            # Create summarization service
            summarization_service = SummarizationService()
        
            # Trigger summarization
            result = summarization_service.trigger_summarization_if_needed(session_id)
        
            logger.info(f"Memory summarization task {self.request.id} completed successfully")
            return result
    except Exception as e:
        logger.error(f"Error in memory summarization task {self.request.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Re-raise the exception to mark the task as failed
        raise

@celery.task(name='tasks.find_similar_memories_task', bind=True)
def find_similar_memories_task(self, text, session_id, limit, min_similarity):
    """Find similar memories asynchronously"""
    try:
        app = get_flask_app()
        with app.app_context():
        
            from app.services.memory_service_enhanced import EnhancedMemoryService
        
            # Create memory service
            memory_service = EnhancedMemoryService()
        
            # Find similar memories
            result = memory_service.retrieve_memories(
                query=text,
                session_id=session_id,
                memory_types=['short_term', 'long_term', 'semantic'],
                limit_per_type=limit
            )
            
            logger.info(f"Memory retrieval task {self.request.id} completed successfully")
            return result
    except Exception as e:
        logger.error(f"Error in memory retrieval task {self.request.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@celery.task(name='tasks.generate_embedding_task', bind=True)
def generate_embedding_task(self, text):
    """Generate embedding vectors asynchronously"""
    try:
        app = get_flask_app()
        with app.app_context():

            from app.services.embedding_service import EmbeddingService
            
            # Create embedding service instance
            embedding_service = EmbeddingService()
            
            # Use the original (sync) method to generate the embedding
            embedding = embedding_service.generate_embedding(text)
            
            logger.info(f"Embedding generation task {self.request.id} completed successfully")
            return embedding
    except Exception as e:
        logger.error(f"Error in embedding generation task {self.request.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@celery.task(name='tasks.store_memory_task', bind=True)
def store_memory_task(self, session_id, content, embedding, task_id, memory_type, 
                     character_id, user_id, importance, metadata):
    """Store a memory with embedding asynchronously"""
    try:
        app = get_flask_app()
        with app.app_context():
            from app.services.memory_service import MemoryService
            from celery.result import AsyncResult
            
            # Wait for embedding result if a task ID was provided
            if embedding is None and task_id is not None:
                embedding_result = AsyncResult(task_id)
                embedding = embedding_result.get(timeout=60)  # Wait up to 60s
            elif embedding is None:
                # Generate embedding here if no task ID
                from app.services.embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                embedding = embedding_service.generate_embedding(content)
            
            # Store memory
            result = MemoryService.store_memory(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata or {}
            )
            
            logger.info(f"Memory storage task {self.request.id} completed successfully")
            return result
    except Exception as e:
        logger.error(f"Error in memory storage task {self.request.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@celery.task(name='tasks.retrieve_memories_task', bind=True)
def retrieve_memories_task(self, current_message, session_id, character_id, max_tokens):
    """
    Retrieve relevant memories for the current context asynchronously
    
    Args:
        current_message (str): The current player message
        session_id (str): The session ID
        character_id (str): The character ID
        max_tokens (int): Maximum number of tokens to include
        
    Returns:
        str: Memory context as formatted text
    """
    try:
        app = get_flask_app()
        with app.app_context():

            from app.services.memory_service_enhanced import EnhancedMemoryService
            memory_service = EnhancedMemoryService()
            
            # Build memory context
            memory_context = memory_service.build_memory_context(
                current_message=current_message,
                session_id=session_id,
                character_id=character_id,
                max_tokens=max_tokens,
                recency_boost=True
            )
            
            logger.info(f"Memory retrieval task {self.request.id} completed successfully")
            return {"success": True, "memory_context": memory_context or ""}
    except Exception as e:
        logger.error(f"Error in memory retrieval task {self.request.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "memory_context": ""}
    


