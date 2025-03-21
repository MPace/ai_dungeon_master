"""
GameSession model
"""
from datetime import datetime
import uuid
from bson.objectid import ObjectId

class GameSession:
    """GameSession model representing a game session with an AI Dungeon Master"""
    
    def __init__(self, session_id=None, character_id=None, user_id=None,
                 history=None, game_state="intro", created_at=None, 
                 updated_at=None, _id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.character_id = character_id
        self.user_id = user_id
        self.history = history or []
        self.game_state = game_state
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._id = _id
    
    @classmethod
    def from_dict(cls, data):
        """Create a GameSession instance from a dictionary"""
        if not data:
            return None
        
        # Convert _id from ObjectId to string if present
        _id = data.get('_id')
        if isinstance(_id, ObjectId):
            _id = str(_id)
        
        return cls(
            session_id=data.get('session_id'),
            character_id=data.get('character_id'),
            user_id=data.get('user_id'),
            history=data.get('history', []),
            game_state=data.get('game_state', 'intro'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _id=_id
        )
    
    def to_dict(self):
        """Convert GameSession instance to a dictionary"""
        return {
            'session_id': self.session_id,
            'character_id': self.character_id,
            'user_id': self.user_id,
            'history': self.history,
            'game_state': self.game_state,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
    
    def add_message(self, sender, message):
        """Add a message to the session history"""
        self.history.append({
            'sender': sender,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()