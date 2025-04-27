# memory_interfaces.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging

from app.services.qdrant_memory_provider import QdrantMemoryProvider
from app.models.memory_vector import MemoryVector

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