# app/models/memory_vector.py
"""
Memory Vector model for use with Qdrant vector database
"""
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional, Union

class MemoryVector:
    """Memory Vector model representing a vectorized memory for the AI Dungeon Master"""
    
    def __init__(self, session_id, content, embedding, memory_type='short_term',
                 character_id=None, user_id=None, importance=5, metadata=None,
                 summary_of=None, memory_id=None, created_at=None, 
                 last_accessed=None, entity_references=None, narrative_context=None):
        """
        Initialize a memory vector
        
        Args:
            session_id (str): Session ID this memory belongs to (or 'semantic' for entity facts)
            content (str): Text content of the memory
            embedding (List[float]): Vector embedding of the content
            memory_type (str): Type of memory - 'episodic_event', 'summary', 'entity_fact', 
                               'short_term' or 'long_term' (for backward compatibility)
            character_id (str, optional): Character ID this memory is related to
            user_id (str, optional): User ID this memory belongs to
            importance (int): Importance score (1-10)
            metadata (Dict, optional): Additional metadata for the memory
            summary_of (List[str], optional): List of memory IDs this memory summarizes
            memory_id (str, optional): Memory ID (generated if not provided)
            created_at (datetime, optional): Creation timestamp
            last_accessed (datetime, optional): Last access timestamp
            entity_references (List[Dict], optional): Entities referenced in this memory
            narrative_context (Dict, optional): Narrative context when memory was created
        """
        self.session_id = session_id
        self.content = content
        self.embedding = embedding
        self.memory_type = memory_type
        self.character_id = character_id
        self.user_id = user_id
        self.importance = importance
        self.metadata = metadata or {}
        self.summary_of = summary_of or []
        self.memory_id = memory_id or str(uuid.uuid4())
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = last_accessed or datetime.utcnow()
        self.entity_references = entity_references or []
        self.narrative_context = narrative_context or {}
        self.is_summarized = False
        self.summary_id = None
    
    @classmethod
    def from_dict(cls, data):
        """Create a MemoryVector instance from a dictionary"""
        if not data:
            return None
        
        entity_references = data.get('entity_references', [])
        narrative_context = data.get('narrative_context', {})
        is_summarized = data.get('is_summarized', False)
        summary_id = data.get('summary_id')
        
        # Create instance
        instance = cls(
            session_id=data.get('session_id'),
            content=data.get('content'),
            embedding=data.get('embedding'),
            memory_type=data.get('memory_type', 'short_term'),
            character_id=data.get('character_id'),
            user_id=data.get('user_id'),
            importance=data.get('importance', 5),
            metadata=data.get('metadata', {}),
            summary_of=data.get('summary_of', []),
            memory_id=data.get('memory_id'),
            created_at=data.get('created_at'),
            last_accessed=data.get('last_accessed'),
            entity_references=entity_references,
            narrative_context=narrative_context
        )
        
        # Set additional fields
        instance.is_summarized = is_summarized
        instance.summary_id = summary_id
        
        return instance
    
    def to_dict(self):
        """Convert MemoryVector instance to a dictionary"""
        return {
            'session_id': self.session_id,
            'content': self.content,
            'embedding': self.embedding,
            'memory_type': self.memory_type,
            'character_id': self.character_id,
            'user_id': self.user_id,
            'importance': self.importance,
            'metadata': self.metadata,
            'summary_of': self.summary_of,
            'memory_id': self.memory_id,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'entity_references': self.entity_references,
            'narrative_context': self.narrative_context,
            'is_summarized': self.is_summarized,
            'summary_id': self.summary_id
        }
    
    def to_qdrant_payload(self):
        """
        Convert MemoryVector to a format suitable for Qdrant payload
        
        Returns:
            Dict[str, Any]: Payload for Qdrant
        """
        # Create payload with all metadata except embedding (which goes in vector)
        payload = {
            'session_id': self.session_id,
            'content': self.content,
            'memory_type': self.memory_type,
            'importance': self.importance,
            'memory_id': self.memory_id,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'is_summarized': self.is_summarized
        }
        
        # Add optional fields if they exist
        if self.character_id:
            payload['character_id'] = self.character_id
            
        if self.user_id:
            payload['user_id'] = self.user_id
            
        if self.metadata:
            payload['metadata'] = self.metadata
            
        if self.summary_of:
            payload['summary_of'] = self.summary_of
            
        if self.summary_id:
            payload['summary_id'] = self.summary_id
            
        # Add new SRD fields
        if self.entity_references:
            payload['entity_references'] = self.entity_references
            
        if self.narrative_context:
            payload['narrative_context'] = self.narrative_context
        
        return payload
    
    @classmethod
    def from_qdrant_result(cls, result):
        """
        Create a MemoryVector from a Qdrant search result
        
        Args:
            result (Dict[str, Any]): Result from Qdrant search
            
        Returns:
            MemoryVector: Memory vector instance
        """
        # Extract core fields
        memory_id = result.get('memory_id')
        embedding = result.get('embedding', [])
        content = result.get('content', '')
        session_id = result.get('session_id', '')
        memory_type = result.get('memory_type', 'short_term')
        entity_references = result.get('entity_references', [])
        narrative_context = result.get('narrative_context', {})
        is_summarized = result.get('is_summarized', False)
        summary_id = result.get('summary_id')
        
        # Create instance
        instance = cls(
            memory_id=memory_id,
            session_id=session_id,
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            character_id=result.get('character_id'),
            user_id=result.get('user_id'),
            importance=result.get('importance', 5),
            metadata=result.get('metadata', {}),
            summary_of=result.get('summary_of', []),
            created_at=result.get('created_at'),
            last_accessed=result.get('last_accessed'),
            entity_references=entity_references,
            narrative_context=narrative_context
        )
        
        # Set additional fields
        instance.is_summarized = is_summarized
        instance.summary_id = summary_id
        
        # Add similarity score if present
        if 'similarity' in result:
            instance.similarity = result['similarity']
        
        return instance
    
    def update_last_accessed(self):
        """Update the last_accessed timestamp to current time"""
        self.last_accessed = datetime.utcnow()
        return self.last_accessed
    
    def calculate_recency_score(self):
        """Calculate a recency score based on how recent the memory is"""
        time_diff = datetime.utcnow() - self.created_at
        days_old = time_diff.total_seconds() / (24 * 3600)
        return max(0.1, 1.0 * (0.9 ** days_old))
    
    def mark_as_summarized(self, summary_id):
        """Mark this memory as having been summarized"""
        self.is_summarized = True
        self.summary_id = summary_id
        return True
    
    def add_entity_reference(self, entity_id, entity_name, entity_type):
        """Add an entity reference to this memory"""
        entity_ref = {
            'entity_id': entity_id,
            'entity_name': entity_name,
            'entity_type': entity_type
        }
        
        # Check if already exists
        for ref in self.entity_references:
            if ref.get('entity_id') == entity_id:
                # Update existing reference
                ref.update(entity_ref)
                return True
        
        # Add new reference
        self.entity_references.append(entity_ref)
        return True
    
    def update_narrative_context(self, context_data):
        """Update narrative context for this memory"""
        self.narrative_context.update(context_data)
        return True
    
    @staticmethod
    def get_memory_type_display(memory_type):
        """Get a human-readable display name for memory types"""
        type_map = {
            'short_term': 'Short Term Memory',
            'long_term': 'Long Term Memory',
            'episodic_event': 'Episodic Memory',
            'summary': 'Summarized Memory',
            'entity_fact': 'Entity Knowledge'
        }
        return type_map.get(memory_type, memory_type.title())