"""
Memory Service
"""
from app.models.memory_vector import MemoryVector
from app.extensions import get_db, get_embedding_service
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for handling memory vector operations"""
    
    @staticmethod
    def store_memory(session_id, content, embedding, memory_type='short_term',
                     character_id=None, user_id=None, importance=5, metadata=None):
        """
        Store a new memory with vector embedding
        
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
            db = get_db()
            if db is None:
                logger.error("Database connection failed when storing memory")
                return {'success': False, 'error': 'Database connection error'}
            
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
            
            # Save to database
            result = db.memory_vectors.insert_one(memory.to_dict())
            
            if result.inserted_id:
                logger.info(f"Memory stored: {memory.memory_id}")
                return {'success': True, 'memory': memory}
            else:
                logger.error("Failed to insert memory")
                return {'success': False, 'error': 'Failed to store memory'}
                
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_similar_memories(embedding, session_id=None, limit=5, min_similarity=0.7):
        """
        Find memories similar to the given embedding
        
        Args:
            embedding (list): Query embedding vector
            session_id (str, optional): Filter by session ID
            limit (int): Maximum number of results
            min_similarity (float): Minimum similarity threshold (0-1)
            
        Returns:
            dict: Result with success status and memories
        """
        try:
            db = get_db()
            if db is None:
                logger.error("Database connection failed when finding memories")
                return {'success': False, 'error': 'Database connection error'}
            
            # Build query
            query = {}
            if session_id:
                query['session_id'] = session_id
            
            # Use MongoDB vector search if available
            try:
                pipeline = [
                    {
                        '$search': {
                            'index': 'vector_index',
                            'vectorSearch': {
                                'queryVector': embedding,
                                'path': 'embedding',
                                'numCandidates': limit * 10,
                                'limit': limit
                            }
                        }
                    },
                    {
                        '$match': query
                    },
                    {
                        '$addFields': {
                            'similarity': {
                                '$vectorDistance': ['$embedding', embedding, 'cosine']
                            }
                        }
                    },
                    {
                        '$match': {
                            'similarity': {'$gte': min_similarity}
                        }
                    },
                    {
                        '$sort': {
                            'similarity': -1
                        }
                    },
                    {
                        '$limit': limit
                    }
                ]
                
                results = list(db.memory_vectors.aggregate(pipeline))
                logger.info(f"Found {len(results)} similar memories using vector search")
                
            except Exception as vector_error:
                logger.warning(f"Vector search failed: {vector_error}. Using fallback method.")
                # Fallback to manual similarity calculation
                results = MemoryService._fallback_similarity_search(db, embedding, query, limit, min_similarity)
            
            # Update lastAccessed timestamp for retrieved memories
            for result in results:
                db.memory_vectors.update_one(
                    {'_id': result['_id']},
                    {'$set': {'last_accessed': datetime.utcnow()}}
                )
            
            # Convert to MemoryVector objects
            memories = [MemoryVector.from_dict(result) for result in results]
            
            return {'success': True, 'memories': memories}
            
        except Exception as e:
            logger.error(f"Error finding similar memories: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _fallback_similarity_search(db, embedding, query, limit, min_similarity):
        """Fallback method for similarity search without vector indexing"""
        logger.warning("Using fallback similarity search - this is less efficient")
        
        # Get all memories matching the query
        memories = list(db.memory_vectors.find(query))
        
        # Calculate cosine similarity manually
        for memory in memories:
            memory_embedding = memory.get('embedding', [])
            memory['similarity'] = MemoryService._cosine_similarity(memory_embedding, embedding)
        
        # Filter by minimum similarity
        memories = [m for m in memories if m.get('similarity', 0) >= min_similarity]
        
        # Sort by similarity and limit results
        memories.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return memories[:limit]
    
    @staticmethod
    def _cosine_similarity(a, b):
        """Calculate cosine similarity between two vectors"""
        if not a or not b:
            return 0
            
        a = np.array(a)
        b = np.array(b)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0
            
        return np.dot(a, b) / (norm_a * norm_b)
    
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
                'summary_type': 'session'
            },
            summary_of=memory_ids
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