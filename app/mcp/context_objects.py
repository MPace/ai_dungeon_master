"""
Model Context Protocol (MCP) Context Objects

This module defines the standard context objects used in the MCP,
which encapsulate different types of context information.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from app.mcp.interfaces import BaseContext

class PlayerContext(BaseContext):
    """Context for player information"""
    
    def __init__(self, user_id: Optional[str] = None, character_id: Optional[str] = None,
                 character_data: Optional[Dict[str, Any]] = None, 
                 preferences: Optional[Dict[str, Any]] = None,
                 context_id: Optional[str] = None):
        self.context_id = context_id or str(uuid.uuid4())
        self.user_id = user_id
        self.character_id = character_id
        self.character_data = character_data or {}
        self.preferences = preferences or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'context_id': self.context_id,
            'context_type': 'player',
            'user_id': self.user_id,
            'character_id': self.character_id,
            'character_data': self.character_data,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerContext':
        """Create from dictionary"""
        # Convert ISO format timestamp to datetime
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            data['created_at'] = datetime.fromisoformat(created_at)
            
        return cls(
            user_id=data.get('user_id'),
            character_id=data.get('character_id'),
            character_data=data.get('character_data', {}),
            preferences=data.get('preferences', {}),
            context_id=data.get('context_id')
        )
    
    def merge(self, other: BaseContext) -> BaseContext:
        """Merge with another context"""
        if not isinstance(other, PlayerContext):
            raise TypeError(f"Cannot merge PlayerContext with {type(other)}")
            
        # Create a new context with merged data
        merged = PlayerContext(
            user_id=self.user_id or other.user_id,
            character_id=self.character_id or other.character_id,
            context_id=self.context_id
        )
        
        # Merge character data
        merged.character_data = {**other.character_data, **self.character_data}
        
        # Merge preferences
        merged.preferences = {**other.preferences, **self.preferences}
        
        return merged
    
class GameContext(BaseContext):
    """Context for game state information"""
    
    def __init__(self, session_id: Optional[str] = None, game_state: str = 'intro',
                 entities: Optional[Dict[str, Any]] = None, 
                 environment: Optional[Dict[str, Any]] = None,
                 player_decisions: Optional[List[Dict[str, Any]]] = None,
                 context_id: Optional[str] = None):
        self.context_id = context_id or str(uuid.uuid4())
        self.session_id = session_id
        self.game_state = game_state
        self.entities = entities or {}
        self.environment = environment or {}
        self.player_decisions = player_decisions or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'context_id': self.context_id,
            'context_type': 'game',
            'session_id': self.session_id,
            'game_state': self.game_state,
            'entities': self.entities,
            'environment': self.environment,
            'player_decisions': self.player_decisions,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameContext':
        """Create from dictionary"""
        # Convert ISO format timestamp to datetime
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            data['created_at'] = datetime.fromisoformat(created_at)
            
        return cls(
            session_id=data.get('session_id'),
            game_state=data.get('game_state', 'intro'),
            entities=data.get('entities', {}),
            environment=data.get('environment', {}),
            player_decisions=data.get('player_decisions', []),
            context_id=data.get('context_id')
        )
    
    def merge(self, other: BaseContext) -> BaseContext:
        """Merge with another context"""
        if not isinstance(other, GameContext):
            raise TypeError(f"Cannot merge GameContext with {type(other)}")
            
        # Create a new context with merged data
        merged = GameContext(
            session_id=self.session_id or other.session_id,
            game_state=self.game_state,  # Use the current game state
            context_id=self.context_id
        )
        
        # Merge entities
        merged.entities = {**other.entities, **self.entities}
        
        # Merge environment data
        merged.environment = {**other.environment, **self.environment}
        
        # Combine player decisions, maintaining chronological order if possible
        all_decisions = self.player_decisions + other.player_decisions
        # Sort by timestamp if available
        all_decisions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        merged.player_decisions = all_decisions
        
        return merged

class MemoryContext(BaseContext):
    """Context for memory information"""
    
    def __init__(self, memories: Optional[List[Dict[str, Any]]] = None,
                 summary: Optional[str] = None,
                 pinned_memories: Optional[List[Dict[str, Any]]] = None,
                 context_id: Optional[str] = None):
        self.context_id = context_id or str(uuid.uuid4())
        self.memories = memories or []
        self.summary = summary or ""
        self.pinned_memories = pinned_memories or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'context_id': self.context_id,
            'context_type': 'memory',
            'memories': self.memories,
            'summary': self.summary,
            'pinned_memories': self.pinned_memories,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryContext':
        """Create from dictionary"""
        # Convert ISO format timestamp to datetime
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            data['created_at'] = datetime.fromisoformat(created_at)
            
        return cls(
            memories=data.get('memories', []),
            summary=data.get('summary', ""),
            pinned_memories=data.get('pinned_memories', []),
            context_id=data.get('context_id')
        )
    
    def merge(self, other: BaseContext) -> BaseContext:
        """Merge with another context"""
        if not isinstance(other, MemoryContext):
            raise TypeError(f"Cannot merge MemoryContext with {type(other)}")
            
        # Create a new context with merged data
        merged = MemoryContext(context_id=self.context_id)
        
        # Combine and deduplicate memories
        all_memories = self.memories + other.memories
        # Use memory_id for deduplication
        unique_memories = {}
        for memory in all_memories:
            memory_id = memory.get('memory_id')
            if memory_id and (memory_id not in unique_memories or 
                             memory.get('last_accessed', '') > unique_memories[memory_id].get('last_accessed', '')):
                unique_memories[memory_id] = memory
        
        merged.memories = list(unique_memories.values())
        
        # Use the newer summary
        if not self.summary and other.summary:
            merged.summary = other.summary
        elif not other.summary:
            merged.summary = self.summary
        else:
            # If both have summaries, use the longer one as it might be more comprehensive
            merged.summary = self.summary if len(self.summary) >= len(other.summary) else other.summary
        
        # Combine and deduplicate pinned memories
        all_pinned = self.pinned_memories + other.pinned_memories
        unique_pinned = {}
        for pinned in all_pinned:
            memory_id = pinned.get('memory_id')
            if memory_id and (memory_id not in unique_pinned or 
                             pinned.get('pinned_at', '') > unique_pinned[memory_id].get('pinned_at', '')):
                unique_pinned[memory_id] = pinned
        
        merged.pinned_memories = list(unique_pinned.values())
        
        return merged
    
class AIPromptContext(BaseContext):
    """Context prepared for AI prompting"""
    
    def __init__(self, system_prompt: str = "", player_message: Optional[str] = None,
                 character_context: Optional[str] = None, game_context: Optional[str] = None,
                 memory_context: Optional[str] = None, conversation_history: Optional[List[Dict[str, Any]]] = None,
                 context_id: Optional[str] = None):
        self.context_id = context_id or str(uuid.uuid4())
        self.system_prompt = system_prompt
        self.player_message = player_message or ""
        self.character_context = character_context or ""
        self.game_context = game_context or ""
        self.memory_context = memory_context or ""
        self.conversation_history = conversation_history or []
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'context_id': self.context_id,
            'context_type': 'ai_prompt',
            'system_prompt': self.system_prompt,
            'player_message': self.player_message,
            'character_context': self.character_context,
            'game_context': self.game_context,
            'memory_context': self.memory_context,
            'conversation_history': self.conversation_history,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIPromptContext':
        """Create from dictionary"""
        # Convert ISO format timestamp to datetime
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            data['created_at'] = datetime.fromisoformat(created_at)
            
        return cls(
            system_prompt=data.get('system_prompt', ""),
            player_message=data.get('player_message', ""),
            character_context=data.get('character_context', ""),
            game_context=data.get('game_context', ""),
            memory_context=data.get('memory_context', ""),
            conversation_history=data.get('conversation_history', []),
            context_id=data.get('context_id')
        )
    
    def merge(self, other: BaseContext) -> BaseContext:
        """Merge with another context"""
        if not isinstance(other, AIPromptContext):
            raise TypeError(f"Cannot merge AIPromptContext with {type(other)}")
            
        # Create a new context with merged data
        merged = AIPromptContext(context_id=self.context_id)
        
        # Use non-empty values from either context, preferring self if both exist
        merged.system_prompt = self.system_prompt or other.system_prompt
        merged.player_message = self.player_message or other.player_message
        
        # For text contexts, concatenate if both have content
        if self.character_context and other.character_context:
            merged.character_context = f"{self.character_context}\n\n{other.character_context}"
        else:
            merged.character_context = self.character_context or other.character_context
            
        if self.game_context and other.game_context:
            merged.game_context = f"{self.game_context}\n\n{other.game_context}"
        else:
            merged.game_context = self.game_context or other.game_context
            
        if self.memory_context and other.memory_context:
            merged.memory_context = f"{self.memory_context}\n\n{other.memory_context}"
        else:
            merged.memory_context = self.memory_context or other.memory_context
        
        # Combine conversation histories
        all_history = self.conversation_history + other.conversation_history
        # Sort by timestamp if available
        all_history.sort(key=lambda x: x.get('timestamp', ''))
        merged.conversation_history = all_history
        
        return merged

class MCPContextFactory:
    """Factory for creating context objects"""
    
    @staticmethod
    def create_context(context_type: str, **kwargs) -> BaseContext:
        """
        Create a context object of the specified type
        
        Args:
            context_type: Type of context to create
            **kwargs: Parameters for the context constructor
            
        Returns:
            BaseContext: The created context object
        """
        context_classes = {
            'player': PlayerContext,
            'game': GameContext,
            'memory': MemoryContext,
            'ai_prompt': AIPromptContext
        }
        
        if context_type not in context_classes:
            raise ValueError(f"Unknown context type: {context_type}")
        
        return context_classes[context_type](**kwargs)