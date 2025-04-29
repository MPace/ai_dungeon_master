# app/services/memory_interfaces.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging

from app.services.qdrant_memory_provider import QdrantMemoryProvider
from app.models.memory_vector import MemoryVector
from app.extensions import get_db

logger = logging.getLogger(__name__)

class BaseMemoryInterface(ABC):
    """Base interface for all memory types with common functionality"""
    
    def __init__(self):
        """Initialize with the Qdrant memory provider"""
        self.provider = QdrantMemoryProvider()
    
    @abstractmethod
    def store(self, content: str, embedding: List[float], **kwargs) -> Dict[str, Any]:
        """Store a memory entry"""
        pass
    
    @abstractmethod
    def retrieve(self, query_embedding: List[float], limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve memories similar to the query embedding"""
        pass
    
    @abstractmethod
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a memory entry"""
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        pass
    
    @classmethod
    def calculate_recency_score(cls, created_at: datetime) -> float:
        """Calculate a recency score based on how recent the memory is"""
        time_diff = datetime.utcnow() - created_at
        days_old = time_diff.total_seconds() / (24 * 3600)
        # Exponential decay - newer memories get higher scores
        return max(0.1, 1.0 * (0.9 ** days_old))
    
    @classmethod
    def combine_relevance_scores(cls, similarity_score: float, recency_score: float, 
                                 importance_score: float) -> float:
        """Combine different relevance factors into a single score"""
        # Default weights - can be adjusted
        similarity_weight = 0.6
        recency_weight = 0.2
        importance_weight = 0.2
        
        return (similarity_score * similarity_weight + 
                recency_score * recency_weight + 
                importance_score * importance_weight)


class ShortTermMemoryInterface(BaseMemoryInterface):
    """Interface for short-term memories that expire after a set period"""
    
    def store(self, content: str, embedding: List[float], session_id: str, 
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              importance: int = 5, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a short-term memory"""
        try:
            # Create memory vector object
            memory = MemoryVector(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type='short_term',
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata or {}
            )
            
            # Store in Qdrant
            success = self.provider.store_memory(memory)
            
            if success:
                return {'success': True, 'memory': memory}
            else:
                return {'success': False, 'error': 'Failed to store memory in Qdrant'}
        
        except Exception as e:
            logger.error(f"Error in ShortTermMemoryInterface.store: {e}")
            return {'success': False, 'error': str(e)}
    
    def retrieve(self, query_embedding: List[float], session_id: str, 
                 limit: int = 5, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Retrieve short-term memories similar to the query embedding"""
        try:
            # Use provider to find similar memories
            memories = self.provider.retrieve_similar_memories(
                query_embedding=query_embedding,
                session_id=session_id,
                memory_type='short_term',
                limit=limit,
                min_similarity=min_similarity
            )
            
            # Convert MemoryVector objects to dictionaries
            return [memory.to_dict() for memory in memories]
        
        except Exception as e:
            logger.error(f"Error in ShortTermMemoryInterface.retrieve: {e}")
            return []
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a short-term memory"""
        try:
            # Get existing memory
            memory = self.provider.get_memory(memory_id)
            
            if memory is None:
                logger.warning(f"Memory not found for update: {memory_id}")
                return False
            
            # Update memory attributes
            for key, value in kwargs.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            # Save updated memory
            return self.provider.update_memory(memory)
        
        except Exception as e:
            logger.error(f"Error in ShortTermMemoryInterface.update: {e}")
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a short-term memory"""
        try:
            return self.provider.delete_memory(memory_id)
        except Exception as e:
            logger.error(f"Error in ShortTermMemoryInterface.delete: {e}")
            return False


class LongTermMemoryInterface(BaseMemoryInterface):
    """Interface for long-term memories that persist indefinitely"""
    
    def store(self, content: str, embedding: List[float], session_id: str, 
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              importance: int = 5, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a long-term memory"""
        try:
            # Create memory vector object
            memory = MemoryVector(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type='long_term',
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata or {}
            )
            
            # Store in Qdrant
            success = self.provider.store_memory(memory)
            
            if success:
                return {'success': True, 'memory': memory}
            else:
                return {'success': False, 'error': 'Failed to store memory in Qdrant'}
        
        except Exception as e:
            logger.error(f"Error in LongTermMemoryInterface.store: {e}")
            return {'success': False, 'error': str(e)}
    
    def retrieve(self, query_embedding: List[float], character_id: str = None, 
                 limit: int = 5, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Retrieve long-term memories similar to the query embedding"""
        try:
            # Use provider to find similar memories
            memories = self.provider.retrieve_similar_memories(
                query_embedding=query_embedding,
                character_id=character_id,
                memory_type='long_term',
                limit=limit,
                min_similarity=min_similarity
            )
            
            # Convert MemoryVector objects to dictionaries
            return [memory.to_dict() for memory in memories]
        
        except Exception as e:
            logger.error(f"Error in LongTermMemoryInterface.retrieve: {e}")
            return []
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a long-term memory"""
        try:
            # Get existing memory
            memory = self.provider.get_memory(memory_id)
            
            if memory is None:
                logger.warning(f"Memory not found for update: {memory_id}")
                return False
            
            # Update memory attributes
            for key, value in kwargs.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            # Save updated memory
            return self.provider.update_memory(memory)
        
        except Exception as e:
            logger.error(f"Error in LongTermMemoryInterface.update: {e}")
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a long-term memory"""
        try:
            return self.provider.delete_memory(memory_id)
        except Exception as e:
            logger.error(f"Error in LongTermMemoryInterface.delete: {e}")
            return False


class SemanticMemoryInterface(BaseMemoryInterface):
    """Interface for semantic memories (concepts, relationships, world knowledge)"""
    
    def store(self, content: str, embedding: List[float], 
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              concept_type: str = 'general', relationships: Optional[List[Dict[str, str]]] = None,
              importance: int = 8, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a semantic memory"""
        try:
            metadata = metadata or {}
            metadata.update({
                'concept_type': concept_type,
                'relationships': relationships or []
            })
            
            # Create memory vector object
            memory = MemoryVector(
                session_id='semantic',  # Using 'semantic' as a special constant
                content=content,
                embedding=embedding,
                memory_type='semantic',
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata
            )
            
            # Store in Qdrant
            success = self.provider.store_memory(memory)
            
            if success:
                return {'success': True, 'memory': memory}
            else:
                return {'success': False, 'error': 'Failed to store memory in Qdrant'}
        
        except Exception as e:
            logger.error(f"Error in SemanticMemoryInterface.store: {e}")
            return {'success': False, 'error': str(e)}
    
    def retrieve(self, query_embedding: List[float], concept_type: Optional[str] = None,
                 character_id: Optional[str] = None, limit: int = 5, 
                 min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Retrieve semantic memories similar to the query embedding"""
        try:
            # Use provider to find similar memories
            memories = self.provider.retrieve_similar_memories(
                query_embedding=query_embedding,
                character_id=character_id,
                memory_type='semantic',
                limit=limit,
                min_similarity=min_similarity
            )
            
            # Filter by concept_type if specified
            if concept_type:
                memories = [m for m in memories if m.metadata.get('concept_type') == concept_type]
            
            # Convert MemoryVector objects to dictionaries
            return [memory.to_dict() for memory in memories]
        
        except Exception as e:
            logger.error(f"Error in SemanticMemoryInterface.retrieve: {e}")
            return []
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a semantic memory"""
        try:
            # Get existing memory
            memory = self.provider.get_memory(memory_id)
            
            if memory is None:
                logger.warning(f"Memory not found for update: {memory_id}")
                return False
            
            # Update memory attributes
            for key, value in kwargs.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            # Save updated memory
            return self.provider.update_memory(memory)
        
        except Exception as e:
            logger.error(f"Error in SemanticMemoryInterface.update: {e}")
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a semantic memory"""
        try:
            return self.provider.delete_memory(memory_id)
        except Exception as e:
            logger.error(f"Error in SemanticMemoryInterface.delete: {e}")
            return False


class WorkingMemoryInterface:
    """
    Interface for working memory (most recent conversation turns) stored in MongoDB
    
    This implementation follows the SRD specification for Working Memory:
    - Stored as a list in the GameSession document
    - Contains raw text of conversations with minimal metadata
    - Simple append/trim lifecycle
    """
    
    def __init__(self):
        """Initialize working memory interface"""
        pass
    
    def add_message(self, session_id: str, sender: str, message: str) -> Dict[str, Any]:
        """
        Add a message to the working memory (conversation history)
        
        Args:
            session_id (str): Session ID
            sender (str): Message sender ('player' or 'dm')
            message (str): Message content
            
        Returns:
            Dict[str, Any]: Result with success status and message
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
                # Ensure history doesn't exceed the configured limit
                self._trim_history_if_needed(session_id)
                logger.info(f"Added message to working memory for session {session_id}")
                return {'success': True, 'message': 'Message added to working memory'}
            else:
                logger.warning(f"Session {session_id} not found, cannot add message")
                return {'success': False, 'error': 'Session not found'}
            
        except Exception as e:
            logger.error(f"Error adding message to working memory: {e}")
            return {'success': False, 'error': str(e)}
    
    def _trim_history_if_needed(self, session_id: str, max_history: int = 20) -> bool:
        """
        Trim history if it exceeds the configured limit
        
        Args:
            session_id (str): Session ID
            max_history (int): Maximum number of messages to keep
            
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
            
            if history_size <= max_history:
                # No trimming needed
                return True
            
            # Calculate how many messages to remove
            remove_count = history_size - max_history
            
            # Remove oldest messages
            result = db.sessions.update_one(
                {'session_id': session_id},
                {'$pop': {'history': -1}}  # -1 pops from the beginning (oldest)
            )
            
            # Repeat if we need to remove more than one
            for _ in range(remove_count - 1):
                db.sessions.update_one(
                    {'session_id': session_id},
                    {'$pop': {'history': -1}}
                )
            
            logger.info(f"Trimmed {remove_count} old messages from session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error trimming history: {e}")
            return False
    
    def get_history(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get recent history from working memory
        
        Args:
            session_id (str): Session ID
            limit (int): Maximum number of messages to retrieve
            
        Returns:
            Dict[str, Any]: Result with success status and history
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when getting history")
                return {'success': False, 'error': 'Database connection error'}
            
            # Get session document
            session = db.sessions.find_one(
                {'session_id': session_id},
                {'history': {'$slice': -limit}}  # Get the last 'limit' elements
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
        Clear the working memory history
        
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
            
            # Clear history in session document
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
    
    def promote_to_episodic(self, session_id: str, index: int, significance: str = '') -> Dict[str, Any]:
        """
        Promote a working memory message to an episodic memory
        
        Args:
            session_id (str): Session ID
            index (int): Index of the message in history to promote
            significance (str, optional): Why this message is significant
            
        Returns:
            Dict[str, Any]: Result with success status and created episodic memory
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed when promoting to episodic memory")
                return {'success': False, 'error': 'Database connection error'}
            
            # Get the session document
            session = db.sessions.find_one(
                {'session_id': session_id},
                {'history': 1, 'character_id': 1, 'user_id': 1}
            )
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return {'success': False, 'error': 'Session not found'}
            
            history = session.get('history', [])
            
            # Check if index is valid
            if index < 0 or index >= len(history):
                logger.warning(f"Invalid index {index} for history of length {len(history)}")
                return {'success': False, 'error': 'Invalid message index'}
            
            # Get the message to promote
            message_entry = history[index]
            
            # Create an episodic memory from this message
            from app.services.memory_service_enhanced import EnhancedMemoryService
            
            memory_service = EnhancedMemoryService()
            
            result = memory_service.store_memory_with_text(
                content=message_entry['message'],
                memory_type='episodic_event',
                session_id=session_id,
                character_id=session.get('character_id'),
                user_id=session.get('user_id'),
                importance=8,  # High importance for promoted memories
                metadata={
                    'sender': message_entry.get('sender'),
                    'timestamp': message_entry.get('timestamp'),
                    'significance': significance,
                    'promoted_from_working_memory': True
                }
            )
            
            if result.get('success', False):
                logger.info(f"Promoted working memory to episodic for session {session_id}")
                return {'success': True, 'memory': result.get('memory')}
            else:
                logger.error(f"Failed to promote working memory: {result.get('error')}")
                return {'success': False, 'error': result.get('error')}
            
        except Exception as e:
            logger.error(f"Error promoting working memory to episodic: {e}")
            return {'success': False, 'error': str(e)}