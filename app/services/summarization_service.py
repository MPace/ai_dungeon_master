"""
Summarization Service using Modal API

This service handles text summarization by using the Modal API
instead of Hugging Face, significantly reducing resource requirements.
"""
from typing import List, Dict, Any, Optional
import logging
import os
import requests
import json
from datetime import datetime, timedelta
from app.extensions import get_embedding_service, get_db
from app.services.memory_service import MemoryService
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

class SummarizationService:
    """Service for abstractive summarization of memories using Modal API"""
    
    def __init__(self, api_url=None, api_token=None):
        """
        Initialize the summarization service with Modal API credentials
        
        Args:
            api_url: The Modal API endpoint URL (optional, defaults to env variable)
            api_token: The Modal API token (optional, defaults to env variable)
        """
        # Get API URL and token from parameters or environment variables
        self.api_url = api_url or os.environ.get("MODAL_API_URL")
        self.api_token = api_token or os.environ.get("MODAL_API_TOKEN")
        print(f"Modal API URL loaded: {self.api_url}")
        
        # Check if we have the required credentials
        if not self.api_url:
            logger.warning("No Modal API URL provided. Summarization will not work.")
        
        if not self.api_token:
            logger.warning("No Modal API token provided. Summarization will not work.")
        
        logger.info(f"Summarization service initialized with Modal API")
    
    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 30, do_sample: bool = False) -> str:
        """
        Summarize a single text using Modal API
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary in tokens
            min_length: Minimum length of the summary in tokens
            
        Returns:
            str: The summarized text, or the original text if summarization fails
        """
        if not self.api_url or not self.api_token:
            logger.error("Modal API credentials not configured")
            return text
            
        try:
            # Truncate text if it's too long - most models have a limit around 4096 tokens
            # This is a simple character-based truncation, tokens would be more accurate
            if len(text) > 4000:  # Conservative limit to ensure we're under model's context window
                logger.info(f"Truncating text from {len(text)} characters to 4000")
                text = text[:4000]
                
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Modal API expects a different format than Hugging Face
            payload = {
                "text": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length,
                    "do_sample": False
                }
            }
            
            logger.info(f"Sending request to: {self.api_url}")
            logger.debug("payload %s", {
                "text": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length,
                    "do_sample": do_sample
                }
            })

            # Send request to API
            logger.debug(f"Sending text to Modal API for summarization: {text[:100]}...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            logger.info("Response status", response.status_code)
            logger.debug("Response body:", response.text)

            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                
                # Handle Modal API response format which might be different from Hugging Face
                if 'summary' in result:
                    return result['summary']
                elif 'result' in result:
                    return result['result']
                elif 'output' in result:
                    return result['output']
                
                # If we can't parse the result, log it and return original text
                logger.warning(f"Unexpected API response format: {response.text[:200]}")
                return text
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return text
                
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return text
    
    def summarize_memories(self, session_id: str, memory_ids: Optional[List[str]] = None, 
                           time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Summarize a group of memories
        
        Args:
            session_id: The session ID to summarize memories for
            memory_ids: Optional list of specific memory IDs to summarize
            time_window: Optional time window to filter memories
            
        Returns:
            dict: Result with success status and summary
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed")
                return {'success': False, 'error': 'Database connection failed'}
            
            if not self.api_url or not self.api_token:
                logger.error("Modal API credentials not configured")
                return {'success': False, 'error': 'Summarization service not properly configured'}
            
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
                logger.info(f"No memories found for session {session_id}")
                return {'success': False, 'error': 'No memories found to summarize'}
                
            # Extract text content from memories
            memory_texts = [memory.get('content', '') for memory in memories]
            
            # Combine texts with markers
            combined_text = "\n".join([f"Memory {i+1}: {text}" for i, text in enumerate(memory_texts)])
            
            logger.info(f"Summarizing {len(memories)} memories for session {session_id}")
            
            # Generate summary
            summary_text = self.summarize_text(combined_text)
            
            # Get embedding service
            embedding_service = get_embedding_service()
            if not embedding_service:
                logger.error("Embedding service not available")
                return {'success': False, 'error': 'Embedding service not available'}
                
            # Generate embedding for summary
            summary_embedding = embedding_service.generate_embedding(summary_text)
            
            # Extract memory IDs
            summary_memory_ids = [memory.get('memory_id', '') for memory in memories if 'memory_id' in memory]
            
            # Create a summary memory
            summary_result = MemoryService.create_memory_summary(
                memory_ids=summary_memory_ids,
                summary_content=summary_text,
                summary_embedding=summary_embedding,
                session_id=session_id,
                character_id=memories[0].get('character_id') if memories else None,
                user_id=memories[0].get('user_id') if memories else None
            )
            
            if summary_result.get('success', False):
                # Get the memory ID - handle both object and dictionary cases for test compatibility
                memory_obj = summary_result.get('memory')
                
                # Determine how to get the memory_id based on the type of memory_obj
                if hasattr(memory_obj, 'memory_id'):
                    # It's an object with attributes
                    summary_id = memory_obj.memory_id
                elif isinstance(memory_obj, dict) and 'memory_id' in memory_obj:
                    # It's a dictionary with a memory_id key
                    summary_id = memory_obj['memory_id']
                else:
                    # Fallback - use a placeholder ID
                    logger.warning("Could not determine memory ID from summary result")
                    summary_id = "unknown"
                
                # Update the summarized memories to mark them as summarized
                for memory_id in summary_memory_ids:
                    db.memory_vectors.update_one(
                        {'memory_id': memory_id},
                        {'$set': {'is_summarized': True, 'summary_id': summary_id}}
                    )
                
                logger.info(f"Successfully summarized {len(memories)} memories into summary ID: {summary_id}")
                return {'success': True, 'summary': memory_obj}
            else:
                logger.error(f"Failed to store summary memory: {summary_result.get('error', 'Unknown error')}")
                return {'success': False, 'error': 'Failed to store summary memory'}
                
        except Exception as e:
            logger.error(f"Error summarizing memories: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def trigger_summarization_if_needed(self, session_id: str) -> Dict[str, Any]:
        """
        Check if summarization is needed and trigger it if so
        
        Args:
            session_id: The session ID to check for summarization
            
        Returns:
            dict: Result with success status and message
        """
        try:
            db = get_db()
            if db is None:
                return {'success': False, 'error': 'Database connection failed'}
                
            # Check volume-based trigger
            memory_count = db.memory_vectors.count_documents({
                'session_id': session_id,
                'memory_type': 'short_term',
                'is_summarized': {'$ne': True}  # Only count non-summarized memories
            })
            
            # Trigger summarization if we have enough memories
            if memory_count >= 10:
                logger.info(f"Triggering summarization for session {session_id} with {memory_count} unsummarized memories")
                time_window = timedelta(minutes=60)
                return self.summarize_memories(session_id, time_window=time_window)
            else:
                logger.debug(f"Summarization not needed for session {session_id} (only {memory_count} unsummarized memories)")
                return {'success': False, 'message': 'Summarization not needed'}
        except Exception as e:
            logger.error(f"Error checking summarization triggers: {e}")
            return {'success': False, 'error': str(e)}