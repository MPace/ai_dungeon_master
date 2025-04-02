"""
Memory Context Provider

This module provides the implementation of the memory context provider,
which retrieves relevant memories for the current context.
"""

import logging
from typing import Dict, Any, List
from app.mcp.interfaces import IContextProvider, BaseContext
from app.mcp.context_objects import MemoryContext

logger = logging.getLogger(__name__)

class MemoryContextProvider(IContextProvider):
    """
    Provider for memory context
    
    This provider retrieves relevant memories for the current context
    using the enhanced memory service.
    """
    
    def get_context(self, request_data: Dict[str, Any]) -> BaseContext:
        """
        Retrieve memory context based on request data
        
        Args:
            request_data: Data required to retrieve the context
                Must contain 'session_id' and should contain 'message' for relevance
                
        Returns:
            MemoryContext: The memory context with relevant memories
        """
        logger.info("Retrieving memory context")
        
        # Extract required data
        session_id = request_data.get('session_id')
        message = request_data.get('message', '')
        
        if not session_id:
            logger.warning("No session_id provided in request data")
            # Return empty context if no session ID
            return MemoryContext()
        
        # Initialize memory service
        from app.services.memory_service_enhanced import EnhancedMemoryService
        memory_service = EnhancedMemoryService()
        
        # Retrieve memories
        memories = []
        summary = ""
        pinned_memories = []
        
        try:
            # Get relevant memories based on message content
            if message:
                logger.debug(f"Retrieving relevant memories for message: {message[:50]}...")
                memory_result = memory_service.retrieve_memories(
                    query=message,
                    session_id=session_id,
                    memory_types=['short_term', 'long_term', 'semantic'],
                    limit_per_type=5
                )
                
                if memory_result.get('success'):
                    # Get combined results
                    memories = memory_result.get('combined_results', [])
                    logger.debug(f"Retrieved {len(memories)} relevant memories")
            
            # Get session summary
            try:
                from app.services.game_service import GameService
                summary_result = GameService.get_session_summary(session_id, request_data.get('user_id'))
                
                if summary_result and summary_result.get('success'):
                    summary = summary_result.get('summary', '')
                    logger.debug(f"Retrieved session summary: {summary[:50]}...")
            except Exception as e:
                logger.error(f"Error retrieving session summary: {e}")
            
            # Get pinned memories
            try:
                from app.services.game_service import GameService
                
                # First get the session to access pinned_memories
                session_result = GameService.get_session(session_id, request_data.get('user_id'))
                
                if session_result and session_result.get('success') and session_result.get('session'):
                    session = session_result.get('session')
                    
                    # Get pinned_memories attribute
                    if hasattr(session, 'pinned_memories'):
                        pinned_memory_refs = session.pinned_memories
                    else:
                        pinned_memory_refs = session.get('pinned_memories', [])
                    
                    # If we have pinned memory references, fetch the actual memories
                    if pinned_memory_refs:
                        pinned_memory_ids = [ref.get('memory_id') for ref in pinned_memory_refs 
                                             if 'memory_id' in ref]
                        
                        # Fetch each memory
                        db = self._get_db()
                        if db is not None:
                            for memory_id in pinned_memory_ids:
                                memory = db.memory_vectors.find_one({'memory_id': memory_id})
                                if memory:
                                    pinned_memories.append(memory)
            except Exception as e:
                logger.error(f"Error retrieving pinned memories: {e}")
        
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
        
        # Create memory context
        logger.info(f"Creating memory context for session_id: {session_id}")
        context = MemoryContext(
            memories=memories,
            summary=summary,
            pinned_memories=pinned_memories
        )
        
        return context
    
    def _get_db(self):
        """Get database connection"""
        try:
            from app.extensions import get_db
            return get_db()
        except Exception as e:
            logger.error(f"Error getting database connection: {e}")
            return None