# app/services/episodic_memory_service.py
"""
Episodic Memory Service

This service manages episodic memories (significant events that occurred during gameplay)
as defined in the SRD. Episodic memories are stored in Qdrant with memory_type 'episodic_event'.
"""
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

from app.models.memory_vector import MemoryVector
from app.extensions import get_embedding_service, get_qdrant_service, get_db

logger = logging.getLogger(__name__)

class EpisodicMemoryService:
    """Service for managing episodic memories (significant events)"""
    
    def __init__(self):
        """Initialize episodic memory service"""
        self.qdrant_service = get_qdrant_service()
        self.embedding_service = get_embedding_service()
    
    def store_episodic_memory(self, content: str, session_id: str,
                           character_id: Optional[str] = None, 
                           user_id: Optional[str] = None,
                           importance: int = 7, 
                           metadata: Optional[Dict[str, Any]] = None,
                           embedding: Optional[List[float]] = None,
                           narrative_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store an episodic memory (significant event)
        
        Args:
            content (str): Memory content
            session_id (str): Session ID
            character_id (str, optional): Character ID
            user_id (str, optional): User ID
            importance (int): Importance score (1-10)
            metadata (dict, optional): Additional metadata
            embedding (list, optional): Vector embedding (generated if not provided)
            narrative_context (dict, optional): Narrative context at the time of the memory
            
        Returns:
            Dict[str, Any]: Result with success status and memory
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Generate embedding if not provided
            if embedding is None:
                if self.embedding_service is None:
                    logger.error("Embedding service not available")
                    return {'success': False, 'error': 'Embedding service not available'}
                
                embedding = self.embedding_service.generate_embedding(content)
            
            # Prepare metadata
            meta = metadata or {}
            meta['created_as'] = meta.get('created_as', 'episodic_memory')
            meta['memory_importance'] = importance
            
            # Extract any entity references from the content
            entity_references = meta.get('entity_references', [])
            if not entity_references:
                entity_references = self._extract_entities(content, session_id)
            
            # Create memory vector
            memory = MemoryVector(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type='episodic_event',
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=meta,
                entity_references=entity_references,
                narrative_context=narrative_context or {}
            )
            
            # Store in Qdrant
            success = self.qdrant_service.store_vector(
                memory_id=memory.memory_id,
                embedding=embedding,
                payload=memory.to_qdrant_payload()
            )
            
            if success:
                logger.info(f"Episodic memory stored: {memory.memory_id}")
                
                # Update important entities in session if entity references exist
                if entity_references and session_id:
                    self._update_session_entities(session_id, entity_references)
                
                return {'success': True, 'memory': memory}
            else:
                logger.error("Failed to store episodic memory")
                return {'success': False, 'error': 'Failed to store episodic memory in Qdrant'}
            
        except Exception as e:
            logger.error(f"Error storing episodic memory: {e}")
            return {'success': False, 'error': str(e)}
    
    def retrieve_similar_memories(self, query: str, session_id: str,
                               limit: int = 5, min_similarity: float = 0.7) -> Dict[str, Any]:
        """
        Retrieve episodic memories similar to the query
        
        Args:
            query (str): Query text
            session_id (str): Session ID
            limit (int): Maximum number of results
            min_similarity (float): Minimum similarity threshold (0-1)
            
        Returns:
            Dict[str, Any]: Result with success status and memories
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Generate embedding for query
            if self.embedding_service is None:
                logger.error("Embedding service not available")
                return {'success': False, 'error': 'Embedding service not available'}
            
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Search for similar memories
            memories = self.qdrant_service.find_similar_vectors(
                query_vector=query_embedding,
                filters={
                    'session_id': session_id,
                    'memory_type': 'episodic_event'
                },
                limit=limit,
                score_threshold=min_similarity
            )
            
            # Convert to memory vectors
            memory_vectors = []
            for memory in memories:
                vector = MemoryVector.from_qdrant_result(memory)
                if hasattr(memory, 'score'):
                    vector.similarity = memory.score
                memory_vectors.append(vector)
            
            logger.info(f"Retrieved {len(memory_vectors)} similar episodic memories")
            return {'success': True, 'memories': memory_vectors}
            
        except Exception as e:
            logger.error(f"Error retrieving similar episodic memories: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_recent_memories(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get the most recent episodic memories
        
        Args:
            session_id (str): Session ID
            limit (int): Maximum number of memories to retrieve
            
        Returns:
            Dict[str, Any]: Result with success status and memories
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Use dummy vector for search (we're filtering by time, not similarity)
            dummy_vector = [0.0] * 768  # Standard size for most embedding models
            
            # Search for memories and sort by creation time
            memories = self.qdrant_service.find_similar_vectors(
                query_vector=dummy_vector,
                filters={
                    'session_id': session_id,
                    'memory_type': 'episodic_event'
                },
                limit=limit,
                score_threshold=0.0  # No similarity threshold
            )
            
            # Convert to memory vectors
            memory_vectors = [MemoryVector.from_qdrant_result(memory) for memory in memories]
            
            # Sort by created_at (newest first)
            memory_vectors.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.min, reverse=True)
            
            # Get the most recent 'limit' memories
            memory_vectors = memory_vectors[:limit]
            
            return {'success': True, 'memories': memory_vectors}
            
        except Exception as e:
            logger.error(f"Error getting recent episodic memories: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_memories_by_entity(self, entity_name: str, session_id: str, 
                            limit: int = 5) -> Dict[str, Any]:
        """
        Get episodic memories related to a specific entity
        
        Args:
            entity_name (str): Entity name
            session_id (str): Session ID
            limit (int): Maximum number of memories to retrieve
            
        Returns:
            Dict[str, Any]: Result with success status and memories
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Find memories referencing this entity
            memories = self.qdrant_service.find_memories_with_entity(
                entity_name=entity_name,
                session_id=session_id,
                limit=limit
            )
            
            # Filter to only episodic memories
            memories = [m for m in memories if getattr(m, 'memory_type', '') == 'episodic_event']
            
            # Convert to memory vectors
            memory_vectors = [MemoryVector.from_qdrant_result(memory) for memory in memories]
            
            return {'success': True, 'memories': memory_vectors}
            
        except Exception as e:
            logger.error(f"Error getting episodic memories by entity: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_unsummarized_memories(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get episodic memories that haven't been summarized yet
        
        Args:
            session_id (str): Session ID
            limit (int): Maximum number of memories to retrieve
            
        Returns:
            Dict[str, Any]: Result with success status and memories
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return {'success': False, 'error': 'Qdrant service not available'}
            
            # Use dummy vector for search (we're not doing similarity search)
            dummy_vector = [0.0] * 768  # Standard size for most embedding models
            
            # Search for memories
            memories = self.qdrant_service.find_similar_vectors(
                query_vector=dummy_vector,
                filters={
                    'session_id': session_id,
                    'memory_type': 'episodic_event',
                    'is_summarized': False
                },
                limit=limit,
                score_threshold=0.0  # No similarity threshold
            )
            
            # Convert to memory vectors
            memory_vectors = [MemoryVector.from_qdrant_result(memory) for memory in memories]
            
            # Sort by created_at (oldest first - important for summarization)
            memory_vectors.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.max)
            
            return {'success': True, 'memories': memory_vectors}
            
        except Exception as e:
            logger.error(f"Error getting unsummarized episodic memories: {e}")
            return {'success': False, 'error': str(e)}
    
    def mark_as_summarized(self, memory_id: str, summary_id: str) -> bool:
        """
        Mark an episodic memory as having been included in a summary
        
        Args:
            memory_id (str): ID of the episodic memory
            summary_id (str): ID of the summary that includes it
            
        Returns:
            bool: Success status
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return False
            
            # Update memory metadata
            result = self.qdrant_service.update_vector_metadata(
                memory_id=memory_id,
                payload={
                    'is_summarized': True,
                    'summary_id': summary_id
                }
            )
            
            if result:
                logger.info(f"Episodic memory {memory_id} marked as summarized")
                return True
            else:
                logger.error(f"Failed to mark episodic memory {memory_id} as summarized")
                return False
            
        except Exception as e:
            logger.error(f"Error marking episodic memory as summarized: {e}")
            return False
    
    def create_from_working_memory(self, session_id: str, index: int, 
                                importance: int = 7, 
                                significance: str = '') -> Dict[str, Any]:
        """
        Create an episodic memory from a working memory entry
        
        Args:
            session_id (str): Session ID
            index (int): Index of the working memory entry
            importance (int): Importance score (1-10)
            significance (str): Why this memory is significant
            
        Returns:
            Dict[str, Any]: Result with success status and memory
        """
        try:
            # Get database connection
            db = get_db()
            if db is None:
                logger.error("Database connection failed")
                return {'success': False, 'error': 'Database connection error'}
            
            # Get session with history
            session = db.sessions.find_one(
                {'session_id': session_id},
                {'history': 1, 'character_id': 1, 'user_id': 1}
            )
            
            if not session:
                logger.warning(f"Session {session_id} not found")
                return {'success': False, 'error': 'Session not found'}
            
            # Check history index
            history = session.get('history', [])
            if index < 0 or index >= len(history):
                logger.warning(f"Invalid history index: {index}")
                return {'success': False, 'error': 'Invalid history index'}
            
            # Get the message
            message = history[index]
            
            # Create episodic memory
            return self.store_episodic_memory(
                content=message.get('message', ''),
                session_id=session_id,
                character_id=session.get('character_id'),
                user_id=session.get('user_id'),
                importance=importance,
                metadata={
                    'sender': message.get('sender'),
                    'timestamp': message.get('timestamp'),
                    'significance': significance,
                    'created_as': 'promoted_from_working_memory'
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating episodic memory from working memory: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete an episodic memory
        
        Args:
            memory_id (str): Memory ID
            
        Returns:
            bool: Success status
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return False
            
            # Delete from Qdrant
            result = self.qdrant_service.delete_vector(memory_id=memory_id)
            
            if result:
                logger.info(f"Episodic memory {memory_id} deleted")
                return True
            else:
                logger.error(f"Failed to delete episodic memory {memory_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting episodic memory: {e}")
            return False
    
    def count_unsummarized_memories(self, session_id: str) -> int:
        """
        Count unsummarized episodic memories for a session
        
        Args:
            session_id (str): Session ID
            
        Returns:
            int: Count of unsummarized memories
        """
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return 0
            
            # Count unsummarized episodic memories
            count = self.qdrant_service.count_vectors({
                'session_id': session_id,
                'memory_type': 'episodic_event',
                'is_summarized': False
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting unsummarized episodic memories: {e}")
            return 0
    
    def _extract_entities(self, content: str, session_id: str) -> List[Dict[str, str]]:
        """
        Extract entity references from content text
        
        Args:
            content (str): Content text
            session_id (str): Session ID for context
            
        Returns:
            List[Dict[str, str]]: List of entity references
        """
        # Simple extraction - find capitalized words
        words = content.split()
        entity_references = []
        
        for i, word in enumerate(words):
            # Look for capitalized words that aren't at the start of sentences
            if len(word) > 2 and word[0].isupper() and word[1:].islower():
                # Skip if it's the first word or after punctuation
                if i > 0 and not words[i-1][-1] in '.!?':
                    # Clean punctuation
                    clean_word = word.strip(',.!?:;\'\"()')
                    if clean_word:
                        entity_type = self._guess_entity_type(clean_word, content)
                        entity_references.append({
                            'entity_name': clean_word,
                            'entity_type': entity_type
                        })
        
        # Get known entities from session
        db = get_db()
        if db:
            session = db.sessions.find_one(
                {'session_id': session_id},
                {'important_entities': 1}
            )
            
            if session and 'important_entities' in session:
                # Check if any known entities are mentioned
                for entity_name, entity_data in session['important_entities'].items():
                    if entity_name in content:
                        # Check if it's already added
                        if not any(ref['entity_name'] == entity_name for ref in entity_references):
                            entity_references.append({
                                'entity_name': entity_name,
                                'entity_type': entity_data.get('type', 'unknown')
                            })
        
        return entity_references
    
    def _guess_entity_type(self, entity_name: str, context: str) -> str:
        """
        Guess entity type based on context
        
        Args:
            entity_name (str): Entity name
            context (str): Context text
            
        Returns:
            str: Guessed entity type
        """
        context_lower = context.lower()
        
        # Check for location indicators
        location_indicators = ['town', 'city', 'village', 'castle', 'fortress', 'inn', 'tavern', 
                              'dungeon', 'cave', 'forest', 'mountain', 'river', 'lake', 'temple']
        for indicator in location_indicators:
            if indicator in context_lower:
                return 'location'
        
        # Check for NPC indicators
        npc_indicators = ['said', 'says', 'spoke', 'man', 'woman', 'elf', 'dwarf', 'halfling', 'gnome', 
                         'merchant', 'guard', 'knight', 'wizard', 'sorcerer', 'priest']
        for indicator in npc_indicators:
            if indicator in context_lower:
                return 'npc'
        
        # Check for item indicators
        item_indicators = ['sword', 'dagger', 'bow', 'staff', 'wand', 'scroll', 'potion',
                          'armor', 'shield', 'amulet', 'ring', 'cloak', 'boots']
        for indicator in item_indicators:
            if indicator in context_lower:
                return 'item'
        
        # Default to unknown
        return 'unknown'
    
    def _update_session_entities(self, session_id: str, entity_references: List[Dict[str, str]]) -> bool:
        """
        Update important entities in the session document
        
        Args:
            session_id (str): Session ID
            entity_references (List[Dict]): Entity references
            
        Returns:
            bool: Success status
        """
        try:
            db = get_db()
            if db is None:
                return False
            
            # Get session document
            session = db.sessions.find_one({'session_id': session_id})
            if not session:
                return False
            
            # Get current important entities
            important_entities = session.get('important_entities', {})
            
            # Update with new entities
            for ref in entity_references:
                entity_name = ref.get('entity_name')
                entity_type = ref.get('entity_type', 'unknown')
                
                if entity_name:
                    if entity_name in important_entities:
                        # Increment importance for repeated mentions
                        entity = important_entities[entity_name]
                        entity['importance'] = min(10, entity.get('importance', 5) + 1)
                        entity['updated_at'] = datetime.utcnow().isoformat()
                    else:
                        # Add new entity
                        important_entities[entity_name] = {
                            'type': entity_type,
                            'description': '',
                            'importance': 5,
                            'created_at': datetime.utcnow().isoformat(),
                            'updated_at': datetime.utcnow().isoformat()
                        }
            
            # Update session document
            db.sessions.update_one(
                {'session_id': session_id},
                {'$set': {'important_entities': important_entities}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session entities: {e}")
            return False