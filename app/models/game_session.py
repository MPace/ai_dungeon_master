"""
Enhanced GameSession model with memory integration
"""
from datetime import datetime
import uuid
from bson.objectid import ObjectId
from typing import List, Dict, Any, Optional

class GameSession:
    """GameSession model representing a game session with an AI Dungeon Master and memory tracking"""
    
    def __init__(self, session_id=None, character_id=None, user_id=None,
                 history=None, game_state="intro", created_at=None, 
                 updated_at=None, pinned_memories=None, session_summary=None,
                 important_entities=None, player_decisions=None, _id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.character_id = character_id
        self.user_id = user_id
        self.history = history or []
        self.game_state = game_state
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # Memory-related additions
        self.pinned_memories = pinned_memories or []  # List of pinned memory IDs
        self.session_summary = session_summary or ""  # Latest session summary
        self.important_entities = important_entities or {}  # Dict of entity_name: {type, description, importance}
        self.player_decisions = player_decisions or []  # List of important player decisions
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
            pinned_memories=data.get('pinned_memories', []),
            session_summary=data.get('session_summary', ''),
            important_entities=data.get('important_entities', {}),
            player_decisions=data.get('player_decisions', []),
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
            'pinned_memories': self.pinned_memories,
            'session_summary': self.session_summary,
            'important_entities': self.important_entities,
            'player_decisions': self.player_decisions
        }
    
    def add_message(self, sender, message):
        """Add a message to the session history"""
        self.history.append({
            'sender': sender,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def pin_memory(self, memory_id, importance=None, note=None):
        """
        Pin a memory to the session for quick reference
        
        Args:
            memory_id (str): The ID of the memory to pin
            importance (int, optional): Optional importance override (1-10)
            note (str, optional): Optional note about why this memory is pinned
        """
        # Check if already pinned
        for pinned in self.pinned_memories:
            if pinned.get('memory_id') == memory_id:
                # Update if needed
                if importance is not None:
                    pinned['importance'] = importance
                if note is not None:
                    pinned['note'] = note
                return
        
        # Add new pinned memory
        self.pinned_memories.append({
            'memory_id': memory_id,
            'pinned_at': datetime.utcnow().isoformat(),
            'importance': importance,
            'note': note
        })
    
    def unpin_memory(self, memory_id):
        """Unpin a memory from the session"""
        self.pinned_memories = [p for p in self.pinned_memories if p.get('memory_id') != memory_id]
    
    def add_important_entity(self, name, entity_type, description, importance=5):
        """
        Add or update an important entity in the session
        
        Args:
            name (str): Entity name
            entity_type (str): Type of entity (NPC, location, item, etc.)
            description (str): Brief description
            importance (int): Importance score (1-10)
        """
        self.important_entities[name] = {
            'type': entity_type,
            'description': description,
            'importance': importance,
            'updated_at': datetime.utcnow().isoformat()
        }
    
    def record_player_decision(self, decision, context=None, impact=None):
        """
        Record an important player decision
        
        Args:
            decision (str): The decision made
            context (str, optional): Context of the decision
            impact (str, optional): Potential impact of the decision
        """
        self.player_decisions.append({
            'decision': decision,
            'context': context,
            'impact': impact,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def update_session_summary(self, summary):
        """Update the session summary"""
        self.session_summary = summary
        self.updated_at = datetime.utcnow()