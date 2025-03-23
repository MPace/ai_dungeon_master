"""
Memory Vector model
"""
from datetime import datetime
import uuid
from bson.objectid import ObjectId

class MemoryVector:
    """Memory Vector model representing a vectorized memory for the AI Dungeon Master"""
    
    def __init__(self, session_id, content, embedding, memory_type='short_term',
                 character_id=None, user_id=None, importance=5, metadata=None,
                 summary_of=None, memory_id=None, created_at=None, 
                 last_accessed=None, _id=None):
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
        self._id = _id
    
    @classmethod
    def from_dict(cls, data):
        """Create a MemoryVector instance from a dictionary"""
        if not data:
            return None
        
        # Convert _id from ObjectId to string if present
        _id = data.get('_id')
        if isinstance(_id, ObjectId):
            _id = str(_id)
        
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
            last_accessed=data.get('last_accessed'),
            _id=_id
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