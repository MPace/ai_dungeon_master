"""
Celery tasks for AI Dungeon Master
"""
from app.celery_config import celery
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='tasks.process_dm_message')
def process_dm_message(self, message, session_id, character_data, user_id):
    """Process a message from the player asynchronously"""
    try:
        from app.services.game_service import GameService
        
        # Process the message
        result = GameService.send_message(session_id, message, user_id)
        
        logger.info(f"Task {self.request.id} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in task {self.request.id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Re-raise the exception to mark the task as failed
        raise

@celery.task(bind=True, name='tasks.generate_memory_summary')
def generate_memory_summary(self, session_id, user_id):
    """Generate a summary of memories for a session"""
    try:
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

@celery.task(bind=True, name='tasks.find_similar_memories_task')
def find_similar_memories_task(self, text, session_id, limit, min_similarity):
    """Find similar memories asynchronously"""
    try:
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

@celery.task(bind=True, name='tasks.generate_embedding_task')
def generate_embedding_task(self, text):
    """Generate embedding vectors asynchronously"""
    try:
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

@celery.task(bind=True, name='tasks.store_memory_task')
def store_memory_task(self, session_id, content, embedding_task_id, memory_type, 
                     character_id, user_id, importance, metadata):
    """Store a memory with embedding asynchronously"""
    try:
        from app.services.memory_service import MemoryService
        from celery.result import AsyncResult
        
        # Wait for embedding result if a task ID was provided
        if embedding_task_id:
            embedding_result = AsyncResult(embedding_task_id)
            embedding = embedding_result.get(timeout=60)  # Wait up to 60s
        else:
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

@celery.task(bind=True, name='tasks.retrieve_memories_task')
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