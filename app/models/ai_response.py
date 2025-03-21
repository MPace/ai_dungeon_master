"""
AIResponse model
"""
from datetime import datetime
import uuid
from bson.objectid import ObjectId

class AIResponse:
    """AIResponse model representing an AI-generated response"""
    
    def __init__(self, response_text, session_id=None, character_id=None, 
                 user_id=None, prompt=None, response_id=None, created_at=None, 
                 model_used=None, tokens_used=None, _id=None):
        self.response_text = response_text
        self.session_id = session_id
        self.character_id = character_id
        self.user_id = user_id
        self.prompt = prompt
        self.response_id = response_id or str(uuid.uuid4())
        self.created_at = created_at or datetime.utcnow()
        self.model_used = model_used
        self.tokens_used = tokens_used
        self._id = _id
    
    @classmethod
    def from_dict(cls, data):
        """Create an AIResponse instance from a dictionary"""
        if not data:
            return None
        
        # Convert _id from ObjectId to string if present
        _id = data.get('_id')
        if isinstance(_id, ObjectId):
            _id = str(_id)
        
        return cls(
            response_text=data.get('response_text'),
            session_id=data.get('session_id'),
            character_id=data.get('character_id'),
            user_id=data.get('user_id'),
            prompt=data.get('prompt'),
            response_id=data.get('response_id'),
            created_at=data.get('created_at'),
            model_used=data.get('model_used'),
            tokens_used=data.get('tokens_used'),
            _id=_id
        )
    
    def to_dict(self):
        """Convert AIResponse instance to a dictionary"""
        return {
            'response_text': self.response_text,
            'session_id': self.session_id,
            'character_id': self.character_id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'response_id': self.response_id,
            'created_at': self.created_at,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used
        }