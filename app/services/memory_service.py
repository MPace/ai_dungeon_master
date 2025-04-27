# app/services/memory_service.py
"""
Memory Service using Qdrant for vector storage
"""
from app.models.memory_vector import MemoryVector
from app.extensions import get_db, get_embedding_service, get_qdrant_service
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for handling memory vector operations using Qdrant"""
    
    @staticmethod
    def store_memory(session_id, content, embedding, memory_type='short_term',
                     character_id=None, user_id=None, importance=5, metadata=None):
        """
        Store a new memory with vector embedding in Qdrant
        
        Args:
            session_id (str): Session ID
            content (str): Memory content text
            embedding (list): Vector embedding of the content
            memory_type (str): Type of memory (short_term, long_term, summary)
            character_id (str, optional): Character ID
            user_id (str, optional): User ID
            importance (int): Importance score (1-10)
            metadata (dict, optional): Additional metadata
            
        Returns:
            dict: Result with success status and memory
        """
        try:
            # Get Qdrant service
            qdrant_service = get_qdrant_service()
            if qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Create memory vector instance
            memory = MemoryVector(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata or {}
            )
            
            # Store in Qdrant
            result = qdrant_service.store_vector(
                memory_id=memory.memory_id,
                embedding=embedding,
                payload=memory.to_qdrant_payload()
            )
            
            if result:
                logger.info(f"Memory stored in Qdrant: {memory.memory_id}")
                return {'success': True, 'memory': memory}
            else:
                logger.error("Failed to store memory in Qdrant")
                return {'success': False, 'error': 'Failed to store memory in Qdrant'}
                
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_similar_memories(embedding, session_id=None, limit=5, min_similarity=0.7):
        """
        Find memories similar to the given embedding using Qdrant
        
        Args:
            embedding (list): Query embedding vector
            session_id (str, optional): Filter by session ID
            limit (int): Maximum number of results
            min_similarity (float): Minimum similarity threshold (0-1)
            
        Returns:
            dict: Result with success status and memories
        """
        try:
            # Get Qdrant service
            qdrant_service = get_qdrant_service()
            if qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Build filter
            filters = {}
            if session_id:
                filters['session_id'] = session_id
            
            # Search for similar vectors
            results = qdrant_service.find_similar_vectors(
                query_vector=embedding,
                filters=filters,
                limit=limit,
                score_threshold=min_similarity
            )
            
            # Convert to MemoryVector objects
            memories = [MemoryVector.from_qdrant_result(result) for result in results]
            
            # Update last_accessed time for each memory
            for memory in memories:
                qdrant_service.update_vector_metadata(
                    memory_id=memory.memory_id,
                    payload={'last_accessed': datetime.utcnow()}
                )
            
            return {'success': True, 'memories': memories}
            
        except Exception as e:
            logger.error(f"Error finding similar memories: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_memory_summary(memory_ids, summary_content, summary_embedding, 
                             session_id, character_id=None, user_id=None):
        """
        Create a summary memory from multiple memory entries
        
        Args:
            memory_ids (list): IDs of memories being summarized
            summary_content (str): Text content of the summary
            summary_embedding (list): Vector embedding of the summary
            session_id (str): Session ID
            character_id (str, optional): Character ID
            user_id (str, optional): User ID
            
        Returns:
            dict: Result with success status and summary memory
        """
        return MemoryService.store_memory(
            session_id=session_id,
            content=summary_content,
            embedding=summary_embedding,
            memory_type='long_term',
            character_id=character_id,
            user_id=user_id,
            importance=8,  # Higher importance for summaries
            metadata={
                'summarized_count': len(memory_ids),
                'is_summary': True,
                'summary_type': 'session',
                'summary_of': memory_ids
            }
        )
    
    @staticmethod
    def store_memory_with_text(session_id, content, memory_type='short_term',
                            character_id=None, user_id=None, importance=5, metadata=None):
        """
        Store a memory with automatically generated embedding
        
        Args:
            session_id (str): Session ID
            content (str): Memory content text
            memory_type (str): Type of memory (short_term, long_term, summary)
            character_id (str, optional): Character ID
            user_id (str, optional): User ID
            importance (int): Importance score (1-10)
            metadata (dict, optional): Additional metadata
            
        Returns:
            dict: Result with success status and memory
        """
        try:
            # Get embedding service
            embedding_service = get_embedding_service()
            if embedding_service is None:
                logger.error("Embedding service not available")
                return {'success': False, 'error': 'Embedding service not available'}
            
            # Generate embedding
            embedding = embedding_service.generate_embedding(content)
            
            # Store memory with embedding
            return MemoryService.store_memory(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata
            )
        
        except Exception as e:
            logger.error(f"Error storing memory with text: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
        
    @staticmethod
    def find_similar_memories_by_text(text, session_id=None, limit=5, min_similarity=0.7):
        """
        Find memories similar to the given text
        
        Args:
            text (str): Query text
            session_id (str, optional): Filter by session ID
            limit (int): Maximum number of results
            min_similarity (float): Minimum similarity threshold (0-1)
            
        Returns:
            dict: Result with success status and memories
        """
        try:
            # Get embedding service
            embedding_service = get_embedding_service()
            if embedding_service is None:
                logger.error("Embedding service not available")
                return {'success': False, 'error': 'Embedding service not available'}
            
            # Generate embedding for the query text
            embedding = embedding_service.generate_embedding(text)
            
            # Find similar memories using the embedding
            return MemoryService.find_similar_memories(
                embedding=embedding,
                session_id=session_id,
                limit=limit,
                min_similarity=min_similarity
            )
        
        except Exception as e:
            logger.error(f"Error finding similar memories by text: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_memory(memory_id):
        """
        Get a memory by ID from Qdrant
        
        Args:
            memory_id (str): Memory ID
            
        Returns:
            dict: Result with success status and memory
        """
        try:
            # Get Qdrant service
            qdrant_service = get_qdrant_service()
            if qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Get vector from Qdrant
            result = qdrant_service.get_vector(memory_id=memory_id)
            
            if result:
                # Convert to MemoryVector
                memory = MemoryVector.from_qdrant_result(result)
                return {'success': True, 'memory': memory}
            else:
                logger.warning(f"Memory {memory_id} not found in Qdrant")
                return {'success': False, 'error': 'Memory not found'}
        
        except Exception as e:
            logger.error(f"Error getting memory: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_memory(memory_id):
        """
        Delete a memory from Qdrant
        
        Args:
            memory_id (str): Memory ID
            
        Returns:
            dict: Result with success status
        """
        try:
            # Get Qdrant service
            qdrant_service = get_qdrant_service()
            if qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Delete from Qdrant
            result = qdrant_service.delete_vector(memory_id=memory_id)
            
            if result:
                logger.info(f"Memory {memory_id} deleted from Qdrant")
                return {'success': True}
            else:
                logger.error(f"Failed to delete memory {memory_id} from Qdrant")
                return {'success': False, 'error': 'Failed to delete memory'}
        
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_memory_metadata(memory_id, metadata):
        """
        Update memory metadata in Qdrant
        
        Args:
            memory_id (str): Memory ID
            metadata (dict): New metadata
            
        Returns:
            dict: Result with success status
        """
        try:
            # Get Qdrant service
            qdrant_service = get_qdrant_service()
            if qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Update metadata in Qdrant
            result = qdrant_service.update_vector_metadata(
                memory_id=memory_id,
                payload={'metadata': metadata}
            )
            
            if result:
                logger.info(f"Memory {memory_id} metadata updated in Qdrant")
                return {'success': True}
            else:
                logger.error(f"Failed to update memory {memory_id} metadata in Qdrant")
                return {'success': False, 'error': 'Failed to update memory metadata'}
        
        except Exception as e:
            logger.error(f"Error updating memory metadata: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}