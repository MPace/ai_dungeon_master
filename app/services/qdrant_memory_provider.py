# app/services/qdrant_memory_provider.py
"""
Qdrant Memory Provider

A provider for storing and retrieving memory vectors using Qdrant
"""
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from app.models.memory_vector import MemoryVector
from app.extensions import get_qdrant_service

logger = logging.getLogger(__name__)

class QdrantMemoryProvider:
    """Provider for Qdrant-based memory storage and retrieval"""
    
    def __init__(self, collection_name="memory_vectors"):
        """Initialize with Qdrant service"""
        self.qdrant_service = get_qdrant_service()
        self.collection_name = collection_name
        
        # If Qdrant service not available, log warning
        if self.qdrant_service is None:
            logger.warning("Qdrant service not available. QdrantMemoryProvider will not function.")
    
    def store_memory(self, memory: MemoryVector) -> bool:
        """
        Store a memory in Qdrant
        
        Args:
            memory (MemoryVector): Memory to store
            
        Returns:
            bool: Success status
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot store memory")
            return False
        
        try:
            # Use the memory's ID and embedding with payload
            payload = memory.to_qdrant_payload()
            result = self.qdrant_service.store_vector(
                memory_id=memory.memory_id,
                embedding=memory.embedding,
                payload=payload
            )
            
            if result:
                logger.info(f"Memory {memory.memory_id} stored in Qdrant")
                return True
            else:
                logger.error(f"Failed to store memory {memory.memory_id} in Qdrant")
                return False
        
        except Exception as e:
            logger.error(f"Error storing memory in Qdrant: {e}")
            return False
    
    def retrieve_similar_memories(self, query_embedding: List[float], 
                                session_id: Optional[str] = None,
                                character_id: Optional[str] = None,
                                memory_type: Optional[Union[str, List[str]]] = None,
                                limit: int = 5,
                                min_similarity: float = 0.7) -> List[MemoryVector]:
        """
        Retrieve similar memories based on vector similarity
        
        Args:
            query_embedding (List[float]): Query vector embedding
            session_id (str, optional): Filter by session ID
            character_id (str, optional): Filter by character ID
            memory_type (str or List[str], optional): Filter by memory type(s)
            limit (int): Maximum number of results
            min_similarity (float): Minimum similarity threshold
            
        Returns:
            List[MemoryVector]: List of similar memory vectors
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot retrieve memories")
            return []
        
        try:
            # Build filters based on provided parameters
            filters = {}
            if session_id:
                filters['session_id'] = session_id
                
            if character_id:
                filters['character_id'] = character_id
                
            if memory_type:
                filters['memory_type'] = memory_type
            
            # Retrieve similar vectors from Qdrant
            results = self.qdrant_service.find_similar_vectors(
                query_vector=query_embedding,
                filters=filters,
                limit=limit,
                score_threshold=min_similarity
            )
            
            # Convert to MemoryVector objects
            memories = [MemoryVector.from_qdrant_result(result) for result in results]
            
            # Update last_accessed for retrieved memories
            for memory in memories:
                memory.update_last_accessed()
                self._update_last_accessed(memory.memory_id)
            
            logger.info(f"Retrieved {len(memories)} similar memories from Qdrant")
            return memories
        
        except Exception as e:
            logger.error(f"Error retrieving similar memories from Qdrant: {e}")
            return []
    
    def _update_last_accessed(self, memory_id: str) -> bool:
        """Update last_accessed timestamp in Qdrant"""
        if self.qdrant_service is None:
            return False
            
        try:
            # Update timestamp in Qdrant
            return self.qdrant_service.update_vector_metadata(
                memory_id=memory_id,
                payload={'last_accessed': datetime.utcnow()}
            )
        except Exception as e:
            logger.error(f"Error updating last_accessed in Qdrant: {e}")
            return False
    
    def get_memory(self, memory_id: str) -> Optional[MemoryVector]:
        """
        Get a memory by ID
        
        Args:
            memory_id (str): Memory ID
            
        Returns:
            Optional[MemoryVector]: Memory vector or None if not found
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot get memory")
            return None
        
        try:
            # Retrieve vector from Qdrant
            result = self.qdrant_service.get_vector(memory_id=memory_id)
            
            if result:
                # Convert to MemoryVector
                memory = MemoryVector.from_qdrant_result(result)
                return memory
            else:
                logger.warning(f"Memory {memory_id} not found in Qdrant")
                return None
        
        except Exception as e:
            logger.error(f"Error getting memory from Qdrant: {e}")
            return None
    
    def update_memory(self, memory: MemoryVector) -> bool:
        """
        Update an existing memory in Qdrant
        
        Args:
            memory (MemoryVector): Memory to update
            
        Returns:
            bool: Success status
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot update memory")
            return False
        
        try:
            # Check if this is just metadata update or a full update
            existing_memory = self.get_memory(memory.memory_id)
            
            if existing_memory is None:
                # Memory doesn't exist, store it
                return self.store_memory(memory)
            
            # Update the vector and payload
            result = self.qdrant_service.store_vector(
                memory_id=memory.memory_id,
                embedding=memory.embedding,
                payload=memory.to_qdrant_payload()
            )
            
            if result:
                logger.info(f"Memory {memory.memory_id} updated in Qdrant")
                return True
            else:
                logger.error(f"Failed to update memory {memory.memory_id} in Qdrant")
                return False
        
        except Exception as e:
            logger.error(f"Error updating memory in Qdrant: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from Qdrant
        
        Args:
            memory_id (str): Memory ID to delete
            
        Returns:
            bool: Success status
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot delete memory")
            return False
        
        try:
            # Delete from Qdrant
            result = self.qdrant_service.delete_vector(memory_id=memory_id)
            
            if result:
                logger.info(f"Memory {memory_id} deleted from Qdrant")
                return True
            else:
                logger.error(f"Failed to delete memory {memory_id} from Qdrant")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting memory from Qdrant: {e}")
            return False
    
    def count_memories(self, session_id: Optional[str] = None, 
                     memory_type: Optional[Union[str, List[str]]] = None,
                     character_id: Optional[str] = None,
                     is_summarized: Optional[bool] = None) -> int:
        """
        Count memories matching the filters
        
        Args:
            session_id (str, optional): Filter by session ID
            memory_type (str or List[str], optional): Filter by memory type(s)
            character_id (str, optional): Filter by character ID
            is_summarized (bool, optional): Filter by summarization status
            
        Returns:
            int: Count of matching memories
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot count memories")
            return 0
        
        try:
            # Build filters
            filters = {}
            if session_id:
                filters['session_id'] = session_id
                
            if memory_type:
                filters['memory_type'] = memory_type
                
            if character_id:
                filters['character_id'] = character_id
                
            if is_summarized is not None:
                filters['is_summarized'] = is_summarized
            
            # Count vectors in Qdrant
            return self.qdrant_service.count_vectors(filters=filters)
        
        except Exception as e:
            logger.error(f"Error counting memories in Qdrant: {e}")
            return 0
            
    def retrieve_episodic_memories(self, session_id: str, limit: int = 10) -> List[MemoryVector]:
        """
        Retrieve episodic memories for a session
        
        Args:
            session_id (str): Session ID
            limit (int): Maximum number of memories to retrieve
            
        Returns:
            List[MemoryVector]: List of episodic memories
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot retrieve episodic memories")
            return []
        
        try:
            # Get memories of type 'episodic_event'
            results = self.qdrant_service.find_memories_by_type(
                memory_type='episodic_event',
                session_id=session_id,
                limit=limit
            )
            
            # Convert to MemoryVector objects
            memories = [MemoryVector.from_qdrant_result(result) for result in results]
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving episodic memories: {e}")
            return []
    
    def retrieve_summarized_memories(self, session_id: str, limit: int = 5) -> List[MemoryVector]:
        """
        Retrieve summarized memories for a session
        
        Args:
            session_id (str): Session ID
            limit (int): Maximum number of memories to retrieve
            
        Returns:
            List[MemoryVector]: List of summary memories
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot retrieve summarized memories")
            return []
        
        try:
            # Get memories of type 'summary'
            results = self.qdrant_service.find_memories_by_type(
                memory_type='summary',
                session_id=session_id,
                limit=limit
            )
            
            # Convert to MemoryVector objects
            memories = [MemoryVector.from_qdrant_result(result) for result in results]
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving summarized memories: {e}")
            return []
    
    def retrieve_entity_facts(self, entity_name: str, limit: int = 5) -> List[MemoryVector]:
        """
        Retrieve facts about a specific entity
        
        Args:
            entity_name (str): Name of the entity
            limit (int): Maximum number of facts to retrieve
            
        Returns:
            List[MemoryVector]: List of entity facts
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot retrieve entity facts")
            return []
        
        try:
            # Get entity facts (type 'entity_fact') referencing this entity
            results = self.qdrant_service.find_memories_with_entity(
                entity_name=entity_name,
                limit=limit
            )
            
            # Convert to MemoryVector objects
            memories = [MemoryVector.from_qdrant_result(result) for result in results]
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving entity facts: {e}")
            return []
    
    def mark_memory_as_summarized(self, memory_id: str, summary_id: str) -> bool:
        """
        Mark a memory as having been summarized
        
        Args:
            memory_id (str): ID of the memory to mark
            summary_id (str): ID of the summary that includes this memory
            
        Returns:
            bool: Success status
        """
        if self.qdrant_service is None:
            logger.error("Qdrant service not available, cannot mark memory as summarized")
            return False
        
        try:
            # Update memory metadata in Qdrant
            result = self.qdrant_service.update_vector_metadata(
                memory_id=memory_id,
                payload={'is_summarized': True, 'summary_id': summary_id}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error marking memory as summarized: {e}")
            return False