# app/models/memory_vector.py
"""
Memory Vector model for use with Qdrant vector database
"""
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

class MemoryVector:
    """Memory Vector model representing a vectorized memory for the AI Dungeon Master"""
    
    def __init__(self, session_id, content, embedding, memory_type='short_term',
                 character_id=None, user_id=None, importance=5, metadata=None,
                 summary_of=None, memory_id=None, created_at=None, 
                 last_accessed=None):
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
        # Removed MongoDB-specific fields (_id, is_in_qdrant)
    
    @classmethod
    def from_dict(cls, data):
        """Create a MemoryVector instance from a dictionary"""
        if not data:
            return None
        
        return cls(
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
            last_accessed=data.get('last_accessed')
        )
    
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
            'last_accessed': self.last_accessed
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
        embedding = result.get('embedding', [])  # This might not be included depending on search
        content = result.get('content', '')
        session_id = result.get('session_id', '')
        memory_type = result.get('memory_type', 'short_term')
        
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
            last_accessed=result.get('last_accessed')
        )
        
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
        # Exponential decay - newer memories get higher scores
        return max(0.1, 1.0 * (0.9 ** days_old))