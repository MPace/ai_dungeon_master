# summarization_service.py
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import numpy as np
from transformers import pipeline
from app.extensions import get_embedding_service

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for abstractive summarization of memories"""
    
    def __init__(self, model_name="facebook/bart-large-cnn"):
        """Initialize the summarization service with a model"""
        self.model_name = model_name
        self.summarizer = None
        try:
            self.summarizer = pipeline("summarization", model=model_name)
            logger.info(f"Summarization model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Error loading summarization model: {e}")
    
    def summarize_text(self, text: str, max_length: int = 100, min_length: int = 30) -> str:
        """Summarize a single text"""
        if not self.summarizer:
            logger.error("Summarizer not initialized")
            return text
            
        try:
            # Truncate text if it's too long for the model
            if len(text) > 1024:
                text = text[:1024]
                
            summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            
            if summary and isinstance(summary, list) and len(summary) > 0:
                return summary[0]['summary_text']
            else:
                return text
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return text
    
    def summarize_memories(self, session_id: str, memory_ids: Optional[List[str]] = None, 
                           time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Summarize a group of memories"""
        from app.services.character_service import get_db_for_service
        db = get_db_for_service()
        if db is None:
            return {'success': False, 'error': 'Database connection failed'}
            
        if not self.summarizer:
            return {'success': False, 'error': 'Summarizer not initialized'}
            
        try:
            # Build query for memories to summarize
            query = {
                'session_id': session_id,
                'memory_type': 'short_term'
            }
            
            # Filter by memory IDs if provided
            if memory_ids:
                query['memory_id'] = {'$in': memory_ids}
                
            # Filter by time window if provided
            if time_window:
                start_time = datetime.utcnow() - time_window
                query['created_at'] = {'$gte': start_time}
                
            # Get memories to summarize
            memories = list(db.memory_vectors.find(query).sort('created_at', 1))
            
            if not memories:
                return {'success': False, 'error': 'No memories found to summarize'}
                
            # Extract text content from memories
            memory_texts = [memory.get('content', '') for memory in memories]
            
            # Combine texts with markers
            combined_text = "\n".join([f"Memory {i+1}: {text}" for i, text in enumerate(memory_texts)])
            
            # Generate summary
            summary_text = self.summarize_text(combined_text)
            
            # Get embedding service
            embedding_service = get_embedding_service()
            if not embedding_service:
                return {'success': False, 'error': 'Embedding service not available'}
                
            # Generate embedding for summary
            summary_embedding = embedding_service.generate_embedding(summary_text)
            
            # Create a summary memory
            from app.services.memory_service import MemoryService
            
            summary_memory_ids = [memory.get('memory_id') for memory in memories if 'memory_id' in memory]
            
            summary_result = MemoryService.create_memory_summary(
                memory_ids=summary_memory_ids,
                summary_content=summary_text,
                summary_embedding=summary_embedding,
                session_id=session_id,
                character_id=memories[0].get('character_id') if memories else None,
                user_id=memories[0].get('user_id') if memories else None
            )
            
            if summary_result['success']:
                # Optionally, update the summarized memories to mark them as summarized
                for memory_id in summary_memory_ids:
                    db.memory_vectors.update_one(
                        {'memory_id': memory_id},
                        {'$set': {'is_summarized': True, 'summary_id': summary_result['memory'].memory_id}}
                    )
                
                return {'success': True, 'summary': summary_result['memory']}
            else:
                return {'success': False, 'error': 'Failed to store summary memory'}
                
        except Exception as e:
            logger.error(f"Error summarizing memories: {e}")
            return {'success': False, 'error': str(e)}
    
    def trigger_summarization_if_needed(self, session_id: str) -> Dict[str, Any]:
        """Check if summarization is needed and trigger it if so"""
        from app.services.memory_service import MemoryService
        
        memory_service = MemoryService()
        
        # Check if summarization should be triggered
        if memory_service.check_summarization_triggers(session_id):
            # Get memories from the last hour
            time_window = timedelta(minutes=60)
            
            # Summarize memories
            return self.summarize_memories(session_id, time_window=time_window)
        else:
            return {'success': False, 'message': 'Summarization not needed'}