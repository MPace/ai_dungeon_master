# app/services/working_memory_service.py
"""
Working Memory Service

This service manages working memory (conversation history) in GameSession.
Working memory represents the most recent conversations between player and DM.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.extensions import get_db
from app.models.game_session import GameSession

logger = logging.getLogger(__name__)

class WorkingMemoryService:
    """Service for managing working memory (conversation history)"""
    
    def __init__(self, max_history: int = 20):
        """
        Initialize working memory service
        
        Args:
            max_history (int): Maximum number of turns to keep in working memory
        """
        self.max_history = max_history
    
    def add_message(self, session_id: str, sender: str, message: str) -> Dict[str, Any]:
        """
        Add a message to working memory
        
        Args:
            session_id (str): Session ID
            sender (str): Message sender ('player' or 'dm')
            message (str): Message content
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when adding message to working memory")
                return {'success': False, 'error': 'Database connection error'}
            
            # Create message entry
            message_entry = {
                'sender': sender,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add to history in the session document
            result = db.sessions.update_one(
                {'session_id': session_id},
                {
                    '$push': {'history': message_entry},
                    '$set': {'updated_at': datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                # Trim history if needed
                self._trim_history_if_needed(session_id)
                logger.info(f"Added {sender} message to working memory for session {session_id}")
                return {'success': True, 'message': 'Message added to working memory'}
            else:
                logger.warning(f"Session {session_id} not found, cannot add message")
                return {'success': False, 'error': 'Session not found'}
            
        except Exception as e:
            logger.error(f"Error adding message to working memory: {e}")
            return {'success': False, 'error': str(e)}
    
    def _trim_history_if_needed(self, session_id: str) -> bool:
        """
        Trim history if it exceeds the configured limit
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: Success status
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when trimming history")
                return False
            
            # Get current history size
            session = db.sessions.find_one(
                {'session_id': session_id},
                {'history': 1}
            )
            
            if not session or 'history' not in session:
                logger.warning(f"Session {session_id} not found or has no history")
                return False
            
            history = session['history']
            history_size = len(history)
            
            if history_size <= self.max_history:
                # No trimming needed
                return True
            
            # Calculate how many messages to remove
            remove_count = history_size - self.max_history
            
            # Remove oldest messages
            for _ in range(remove_count):
                db.sessions.update_one(
                    {'session_id': session_id},
                    {'$pop': {'history': -1}}  # -1 pops from the beginning (oldest)
                )
            
            logger.info(f"Trimmed {remove_count} old messages from session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error trimming history: {e}")
            return False
    
    def get_history(self, session_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get working memory history
        
        Args:
            session_id (str): Session ID
            limit (int, optional): Maximum number of messages to retrieve
                                 (defaults to self.max_history if None)
            
        Returns:
            Dict[str, Any]: Result with success status and history
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when getting history")
                return {'success': False, 'error': 'Database connection error'}
            
            # Use the class limit if not specified
            if limit is None:
                limit = self.max_history
            
            # Get session document with history
            projection = {'history': {'$slice': -limit}}  # Get the last 'limit' elements
            session = db.sessions.find_one(
                {'session_id': session_id},
                projection
            )
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return {'success': False, 'error': 'Session not found'}
            
            history = session.get('history', [])
            
            return {'success': True, 'history': history}
            
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return {'success': False, 'error': str(e)}
    
    def clear_history(self, session_id: str) -> Dict[str, Any]:
        """
        Clear working memory history
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when clearing history")
                return {'success': False, 'error': 'Database connection error'}
            
            # Clear history array in session document
            result = db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {'history': [], 'updated_at': datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Cleared history for session {session_id}")
                return {'success': True, 'message': 'History cleared successfully'}
            else:
                logger.warning(f"Session {session_id} not found, cannot clear history")
                return {'success': False, 'error': 'Session not found'}
            
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return {'success': False, 'error': str(e)}
    
    def compress_history(self, session_id: str, max_tokens: int) -> Dict[str, Any]:
        """
        Compress working memory history to fit within token budget
        
        Args:
            session_id (str): Session ID
            max_tokens (int): Maximum token budget
            
        Returns:
            Dict[str, Any]: Result with success status and compressed history
        """
        try:
            # Get the current history
            history_result = self.get_history(session_id)
            if not history_result.get('success', False):
                return history_result
            
            history = history_result.get('history', [])
            
            # If history is empty, nothing to compress
            if not history:
                return {'success': True, 'history': []}
            
            # Estimate tokens in current history
            current_tokens = self._estimate_tokens(history)
            
            # If already within budget, return as is
            if current_tokens <= max_tokens:
                return {'success': True, 'history': history}
            
            # Strategy 1: Trim oldest messages until we fit
            compressed_history = history.copy()
            while compressed_history and self._estimate_tokens(compressed_history) > max_tokens:
                compressed_history.pop(0)  # Remove oldest message
            
            # If we still have messages, return the trimmed history
            if compressed_history:
                logger.info(f"Compressed history from {len(history)} to {len(compressed_history)} messages")
                return {'success': True, 'history': compressed_history}
            
            # Strategy 2: If we've trimmed everything, keep just the most recent exchange
            if len(history) >= 2:
                last_two = history[-2:]
                if self._estimate_tokens(last_two) <= max_tokens:
                    logger.info("Compressed to just the most recent exchange")
                    return {'success': True, 'history': last_two}
            
            # Strategy 3: Keep only the most recent message
            last_message = [history[-1]]
            if self._estimate_tokens(last_message) <= max_tokens:
                logger.info("Compressed to just the most recent message")
                return {'success': True, 'history': last_message}
            
            # Strategy 4: Truncate the last message
            if history:
                last_msg = history[-1].copy()
                message_text = last_msg.get('message', '')
                tokens_per_char = 0.25  # Rough estimate of tokens per character
                max_chars = int(max_tokens / tokens_per_char)
                
                if len(message_text) > max_chars:
                    last_msg['message'] = message_text[:max_chars] + '...'
                    logger.info("Truncated the last message to fit token budget")
                    return {'success': True, 'history': [last_msg]}
            
            # If all strategies fail, return an empty history
            logger.warning("Could not compress history to fit token budget, returning empty history")
            return {'success': True, 'history': []}
            
        except Exception as e:
            logger.error(f"Error compressing history: {e}")
            return {'success': False, 'error': str(e)}
    
    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Estimate the number of tokens in a list of messages
        
        Args:
            messages (List[Dict]): List of message entries
            
        Returns:
            int: Estimated token count
        """
        total_chars = 0
        
        for msg in messages:
            # Count characters in message text
            message_text = msg.get('message', '')
            total_chars += len(message_text)
            
            # Add sender (typically 'player' or 'dm')
            sender = msg.get('sender', '')
            total_chars += len(sender)
            
            # Add some overhead for formatting
            total_chars += 10
        
        # Rough estimate: 1 token ≈ 4 characters
        tokens = total_chars // 4
        
        return tokens
    
    def extract_entities_from_history(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Extract potential entity names from recent history
        
        Args:
            session_id (str): Session ID
            limit (int): Maximum number of recent messages to analyze
            
        Returns:
            Dict[str, Any]: Result with success status and extracted entities
        """
        try:
            # Get recent history
            history_result = self.get_history(session_id, limit)
            if not history_result.get('success', False):
                return history_result
            
            history = history_result.get('history', [])
            
            # Extract entities (simplified - a more sophisticated NLP approach would be better)
            entities = set()
            
            for msg in history:
                message_text = msg.get('message', '')
                words = message_text.split()
                
                for i, word in enumerate(words):
                    # Look for capitalized words that aren't at the start of sentences
                    if len(word) > 2 and word[0].isupper() and word[1:].islower():
                        # Skip if it's the first word in the message or after punctuation
                        if i > 0 and not words[i-1][-1] in '.!?':
                            # Clean punctuation
                            clean_word = word.strip(',.!?:;\'\"()')
                            if clean_word:
                                entities.add(clean_word)
            
            return {'success': True, 'entities': list(entities)}
            
        except Exception as e:
            logger.error(f"Error extracting entities from history: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_session_with_compressed_history(self, session_id: str, compressed_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update the session with compressed history
        
        Args:
            session_id (str): Session ID
            compressed_history (List[Dict]): Compressed history to save
            
        Returns:
            Dict[str, Any]: Result with success status
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when updating compressed history")
                return {'success': False, 'error': 'Database connection error'}
            
            # Update history in session document
            result = db.sessions.update_one(
                {'session_id': session_id},
                {
                    '$set': {
                        'history': compressed_history,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated session {session_id} with compressed history ({len(compressed_history)} messages)")
                return {'success': True, 'message': 'History updated successfully'}
            else:
                logger.warning(f"Session {session_id} not found, cannot update history")
                return {'success': False, 'error': 'Session not found'}
            
        except Exception as e:
            logger.error(f"Error updating compressed history: {e}")
            return {'success': False, 'error': str(e)}