# app/services/memory_service_enhanced.py
"""
Enhanced Memory Service using Qdrant

This service provides extended memory functionality using Qdrant for vector storage.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from app.models.memory_vector import MemoryVector
from app.extensions import get_embedding_service, get_qdrant_service
from app.services.memory_interfaces import ShortTermMemoryInterface, LongTermMemoryInterface, SemanticMemoryInterface

logger = logging.getLogger(__name__)

class EnhancedMemoryService:
    """Enhanced service for memory management with extended functionality"""
    
    def __init__(self):
        """Initialize memory interfaces"""
        self.short_term = ShortTermMemoryInterface()
        self.long_term = LongTermMemoryInterface()
        self.semantic = SemanticMemoryInterface()
        self.qdrant_service = get_qdrant_service()
    
    def store_memory_with_text(self, content: str, memory_type: str = 'short_term', 
                           session_id: Optional[str] = None, 
                           character_id: Optional[str] = None, 
                           user_id: Optional[str] = None,
                           importance: int = 5, 
                           metadata: Optional[Dict[str, Any]] = None,
                           async_mode: bool = True) -> Dict[str, Any]:
        """Store a memory with automatic embedding generation"""
        # Get embedding service
        embedding_service = get_embedding_service()
        if embedding_service is None:
            logger.error("Embedding service not available")
            return {'success': False, 'error': 'Embedding service not available'}
        
        if async_mode:
            # Generate embedding asynchronously
            task_id = embedding_service.generate_embedding_async(content)
            
            # Submit storage task
            from app.tasks import store_memory_task
            storage_task = store_memory_task.delay(
                session_id, content, None, task_id, memory_type, 
                character_id, user_id, importance, metadata,
            )
            
            return {'success': True, 'task_id': storage_task.id}
        else:
            # Generate embedding
            embedding = embedding_service.generate_embedding(content)
            
            # Store memory based on type
            if memory_type == 'short_term':
                if not session_id:
                    return {'success': False, 'error': 'Session ID required for short-term memories'}
                return self.short_term.store(
                    content=content,
                    embedding=embedding,
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    importance=importance,
                    metadata=metadata
                )
            elif memory_type == 'long_term':
                if not session_id:
                    return {'success': False, 'error': 'Session ID required for long-term memories'}
                return self.long_term.store(
                    content=content,
                    embedding=embedding,
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    importance=importance,
                    metadata=metadata
                )
            elif memory_type == 'semantic':
                concept_type = metadata.get('concept_type', 'general') if metadata else 'general'
                relationships = metadata.get('relationships', []) if metadata else []
                
                return self.semantic.store(
                    content=content,
                    embedding=embedding,
                    character_id=character_id,
                    user_id=user_id,
                    concept_type=concept_type,
                    relationships=relationships,
                    importance=importance,
                    metadata=metadata
                )
            else:
                logger.error(f"Unknown memory type: {memory_type}")
                return {'success': False, 'error': f'Unknown memory type: {memory_type}'}
    
    def retrieve_memories(self, query: str, session_id: Optional[str] = None, 
                          character_id: Optional[str] = None,
                          memory_types: List[str] = ['short_term', 'long_term', 'semantic'],
                          limit_per_type: int = 3, min_similarity: float = 0.7) -> Dict[str, Any]:
        """Retrieve memories across different memory types"""
        logger.info(f"Retrieving memories for query: '{query[:30]}...' in session {session_id}")
    
        # Get embedding service
        embedding_service = get_embedding_service()
        if embedding_service is None:
            logger.error("Embedding service not available")
            return {'success': False, 'error': 'Embedding service not available'}
        
        # Generate embedding for query
        query_embedding = embedding_service.generate_embedding(query)
        logger.info(f"Vector query initiated with embedding of dimension {len(query_embedding)}")

        results = {}
        all_memories = []
        
        # Retrieve memories from each requested type
        if 'short_term' in memory_types and session_id:
            logger.info("Retrieving short-term memories")
            short_term_memories = self.short_term.retrieve(
                query_embedding=query_embedding,
                session_id=session_id,
                limit=limit_per_type,
                min_similarity=min_similarity
            )
            results['short_term'] = short_term_memories
            all_memories.extend([(memory, 'short_term') for memory in short_term_memories])
            logger.info(f"Retrieved {len(short_term_memories)} short-term memories")


        if 'long_term' in memory_types:
            long_term_memories = self.long_term.retrieve(
                query_embedding=query_embedding,
                character_id=character_id,
                limit=limit_per_type,
                min_similarity=min_similarity
            )
            results['long_term'] = long_term_memories
            all_memories.extend([(memory, 'long_term') for memory in long_term_memories])
        
        if 'semantic' in memory_types:
            semantic_memories = self.semantic.retrieve(
                query_embedding=query_embedding,
                character_id=character_id,
                limit=limit_per_type,
                min_similarity=min_similarity
            )
            results['semantic'] = semantic_memories
            all_memories.extend([(memory, 'semantic') for memory in semantic_memories])
        
        # Sort all memories by similarity
        all_memories.sort(key=lambda x: x[0].get('similarity', 0), reverse=True)

        return {
            'success': True,
            'results_by_type': results,
            'combined_results': [memory for memory, _ in all_memories[:limit_per_type * len(memory_types)]]
        }
    
    def build_memory_context(self, current_message: str, session_id: str, 
                            character_id: Optional[str] = None,
                            max_tokens: int = 1000,
                            recency_boost: bool = True) -> str:
        """Build a memory context for AI prompts"""
        # Get embedding service
        embedding_service = get_embedding_service()
        if embedding_service is None:
            logger.error("Embedding service not available for context building")
            return ""
        
        try:
            # Generate embedding for current message
            query_embedding = embedding_service.generate_embedding(current_message)
            logger.info(f"Generated query embedding with {len(query_embedding)} dimensions")

            # Get pinned memories
            pinned_memories = self._get_pinned_memories(session_id)
            
            # Get any summary if available
            summary = self._get_session_summary(session_id)

            # Retrieve relevant memories using all memory types
            memories_result = self.retrieve_memories(
                query=current_message,
                session_id=session_id,
                character_id=character_id,
                memory_types=['short_term', 'long_term', 'semantic'],
                limit_per_type=5
            )
        
            if not memories_result['success']:
                return ""
            
            combined_memories = memories_result['combined_results']
            
            # Add pinned memories to combined memories, avoid duplicates by checking memory_id
            existing_ids = {memory.get('memory_id') for memory in combined_memories if 'memory_id' in memory}
            for memory in pinned_memories:
                if memory.get('memory_id') not in existing_ids:
                    combined_memories.append(memory)
                    existing_ids.add(memory.get('memory_id'))

            # Sort memories by relevance
            if recency_boost:
                # Calculate scores with recency boost
                for memory in combined_memories:
                    created_at = memory.get('created_at')
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at)
                        except ValueError:
                            created_at = datetime.utcnow() - timedelta(days=7)  # Default to a week ago
                    
                    recency_score = self.short_term.calculate_recency_score(created_at)
                    similarity_score = memory.get('similarity', 0.5)
                    importance_score = min(1.0, memory.get('importance', 5) / 10.0)
                    
                    memory['combined_score'] = self.short_term.combine_relevance_scores(
                        similarity_score, recency_score, importance_score
                    )
                
                # Sort by combined score
                combined_memories.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            
            # Build context
            context_parts = []
            token_count = 0

            # Add summary first if available
            if summary:
                summary_tokens = self._estimate_tokens(summary)
                summary_max = max_tokens // 4  # Use up to 25% of the token budget for summary

                if summary_tokens <= summary_max:
                    context_parts.append("## CAMPAIGN SUMMARY:\n" + summary)
                    token_count += summary_tokens

            # Add pinned memories with higher priority
            pinned_memory_ids = {memory.get('memory_id') for memory in pinned_memories}
            pinned_header_added = False 
        
            for memory in combined_memories:
                if token_count >= max_tokens:
                    break

                if memory.get('memory_id') in pinned_memory_ids:
                    memory_text = memory.get('content', '')
                
                    if not pinned_header_added:
                        context_parts.append("## PINNED MEMORIES:")
                        pinned_header_added = True
                        token_count += 3

                    memory_entry = f"PINNED: {memory_text}"
                    memory_tokens = self._estimate_tokens(memory_entry)

                    if token_count + memory_tokens <= max_tokens:
                        context_parts.append(memory_entry)
                        token_count += memory_tokens

            # Add other memories based on relevance
            memory_header_added = False
            for memory in combined_memories:
                if token_count >= max_tokens:
                    break
                    
                # Skip pinned memories as they're already added
                if memory.get('memory_id') in pinned_memory_ids:
                    continue

                memory_text = memory.get('content', '')
                memory_type = memory.get('memory_type', 'unknown')
                metadata = memory.get('metadata', {})

                if memory_type == 'long_term' and metadata.get('is_summary') == True:
                    prefix = "Session Summary: "
                elif memory_type == 'short_term':
                    prefix = "Recent Memory: "
                elif memory_type == 'long_term':
                    prefix = "Important memory: "
                elif memory_type == 'semantic':
                    prefix = "Known fact: "
                else:
                    prefix = "Memory: "

                memory_entry = f"{prefix}{memory_text}"
                memory_tokens = self._estimate_tokens(memory_entry)
            
                if token_count + memory_tokens <= max_tokens:
                    if not memory_header_added:
                        context_parts.append("## RELEVANT MEMORIES:")
                        memory_header_added = True
                        token_count += 3
                    
                    context_parts.append(memory_entry)
                    token_count += memory_tokens
                else:
                    break
        
            context_text = "\n\n".join(context_parts)
            logger.info(f"Returning memory context with {len(context_parts)} sections, ~{token_count} tokens")
            return context_text

        except Exception as e:
            logger.error(f"Error building memory context: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""
    
    def _get_pinned_memories(self, session_id: str) -> List[Dict[str, Any]]:
        """Get pinned memories for a session from Qdrant based on session metadata"""
        try:
            if self.qdrant_service is None:
                return []
                
            # Get session data from MongoDB to find pinned memory IDs
            from app.extensions import get_db
            db = get_db()
            if db is None:
                return []
                
            session_data = db.sessions.find_one({'session_id': session_id})
            if not session_data or 'pinned_memories' not in session_data:
                return []
                
            pinned_refs = session_data['pinned_memories']
            
            # Extract memory IDs
            memory_ids = [ref['memory_id'] for ref in pinned_refs if 'memory_id' in ref]
            
            # Retrieve each memory from Qdrant
            pinned_memories = []
            for memory_id in memory_ids:
                result = self.qdrant_service.get_vector(memory_id)
                if result:
                    pinned_memories.append(result)
            
            return pinned_memories
            
        except Exception as e:
            logger.error(f"Error getting pinned memories: {e}")
            return []
    
    def _get_session_summary(self, session_id: str) -> str:
        """Get the session summary from MongoDB"""
        try:
            from app.extensions import get_db
            db = get_db()
            if db is None:
                return ""
                
            session_data = db.sessions.find_one({'session_id': session_id})
            if not session_data or 'session_summary' not in session_data:
                return ""
                
            return session_data['session_summary']
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return ""
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text"""
        if not text:
            return 0
        
        # Simple estimation - about 4 chars per token on average
        return len(text) // 4
    
    def promote_to_long_term(self, memory_id: str) -> bool:
        """Promote a short-term memory to long-term"""
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return False
                
            # Get the memory from Qdrant
            result = self.qdrant_service.get_vector(memory_id)
            if not result:
                logger.error(f"Memory not found: {memory_id}")
                return False
                
            # Create memory vector object
            memory = MemoryVector.from_qdrant_result(result)
            
            # Change memory type
            memory.memory_type = 'long_term'
            
            # Store as long-term memory
            success = self.qdrant_service.store_vector(
                memory_id=memory.memory_id,
                embedding=memory.embedding,
                payload=memory.to_qdrant_payload()
            )
            
            if success:
                logger.info(f"Memory {memory_id} promoted to long-term")
                return True
            else:
                logger.error(f"Failed to promote memory {memory_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error promoting memory to long-term: {e}")
            return False
    
    def check_summarization_triggers(self, session_id: str) -> bool:
        """Check if summarization should be triggered for a session"""
        try:
            if self.qdrant_service is None:
                logger.error("Qdrant service not available")
                return False
                
            # Check volume-based trigger
            filters = {
                'session_id': session_id,
                'memory_type': 'short_term'
            }
            memory_count = self.qdrant_service.count_vectors(filters)
            
            if memory_count >= 50:  # Adjust threshold as needed
                return True
                
            # Check time-based trigger
            # Note: Since we can't easily find the oldest memory in Qdrant without
            # retrieving all memories, we'll just use the volume-based approach for now.
            # With sufficiently high message volume, time-based summary will be triggered naturally.
            
            return False
        except Exception as e:
            logger.error(f"Error checking summarization triggers: {e}")
            return False
    
    def store_memory_with_text_async(self, content: str, memory_type: str = 'short_term', 
                               session_id: Optional[str] = None, 
                               character_id: Optional[str] = None, 
                               user_id: Optional[str] = None,
                               importance: int = 5, 
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a memory asynchronously and return task ID
        
        Args:
            Same as store_memory_with_text
            
        Returns:
            str: Task ID for retrieving the result later
        """
        from app.tasks import store_memory_task
        
        # Submit task
        task = store_memory_task.delay(
            session_id, content, None, None, memory_type, 
            character_id, user_id, importance, metadata
        )
        
        return task.id

    def retrieve_memories_async(self, query: str, session_id: Optional[str] = None, 
                            memory_types: List[str] = ['short_term', 'long_term', 'semantic'],
                            limit_per_type: int = 3, min_similarity: float = 0.7) -> str:
        """
        Retrieve memories asynchronously and return task ID
        
        Args:
            Same as retrieve_memories
            
        Returns:
            str: Task ID for retrieving the result later
        """
        from app.tasks import find_similar_memories_task
        
        # Submit task
        task = find_similar_memories_task.delay(
            query, session_id, limit_per_type, min_similarity
        )
        
        return task.id