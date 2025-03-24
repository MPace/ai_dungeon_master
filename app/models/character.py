"""
Character model
"""
from datetime import datetime
import uuid
from bson.objectid import ObjectId

class Character:
    """Character model representing a player character"""
    
    def __init__(self, name, race, character_class, background, level=1,
                 abilities=None, skills=None, equipment=None, features=None,
                 spellcasting=None, hit_points=None, description=None,
                 user_id=None, character_id=None, created_at=None, 
                 updated_at=None, last_played=None, is_draft=False, 
                 completed_at=None, _id=None):
        self.name = name
        self.race = race
        self.character_class = character_class
        self.background = background
        self.level = level
        self.abilities = abilities or {
            'strength': 10,
            'dexterity': 10,
            'constitution': 10,
            'intelligence': 10,
            'wisdom': 10,
            'charisma': 10
        }
        self.skills = skills or []
        self.equipment = equipment or {}
        self.features = features or {}
        self.spellcasting = spellcasting or {}
        self.hit_points = hit_points or {}
        self.description = description or ""
        self.user_id = user_id
        self.character_id = character_id or str(uuid.uuid4())
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_played = last_played
        self.is_draft = is_draft
        self.completed_at = completed_at
        self._id = _id
    
    @classmethod
    def from_dict(cls, data):
        """Create a Character instance from a dictionary"""
        if not data:
            return None
        
        if 'character_id' not in data or not data['character_id']:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Skipping character record missing character_id: {data.get('_id')}")
            return None
        
        # Convert _id from ObjectId to string if present
        _id = data.get('_id')
        if isinstance(_id, ObjectId):
            _id = str(_id)
        
        # Map 'class' key to 'character_class' attribute
        character_class = data.get('class')
        if not character_class and 'character_class' in data:
            character_class = data.get('character_class')
        
        # Map 'isDraft' to 'is_draft'
        is_draft = data.get('isDraft', False)
        
        # Get other fields with appropriate defaults
        abilities = data.get('abilities', {})
        skills = data.get('skills', [])
        
        return cls(
            name=data.get('name', ''),
            race=data.get('race', ''),
            character_class=character_class,
            background=data.get('background', ''),
            level=data.get('level', 1),
            abilities=abilities,
            skills=skills,
            equipment=data.get('equipment', {}),
            features=data.get('features', {}),
            spellcasting=data.get('spellcasting', {}),
            hit_points=data.get('hitPoints', {}),
            description=data.get('description', ''),
            user_id=data.get('user_id'),
            character_id=data.get('character_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            last_played=data.get('last_played'),
            is_draft=is_draft,
            completed_at=data.get('completedAt'),
            _id=_id
        )
    
    def to_dict(self):
        """Convert Character instance to a dictionary for JSON serialization"""
        # First get the base dictionary with standard attributes
        data = {
            'name': self.name,
            'race': self.race,
            'class': self.character_class,  # Use 'class' key for frontend compatibility
            'background': self.background,
            'level': self.level,
            'abilities': self.abilities,
            'skills': self.skills,
            'equipment': self.equipment,
            'features': self.features,
            'spellcasting': self.spellcasting,
            'hitPoints': self.hit_points,  # Use 'hitPoints' for frontend compatibility
            'description': self.description,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at,
            'last_played': self.last_played.isoformat() if hasattr(self.last_played, 'isoformat') and self.last_played else None,
            'isDraft': self.is_draft,  # Use 'isDraft' for frontend compatibility
        }
        
        # Add completed_at only if it exists
        if self.completed_at:
            data['completedAt'] = self.completed_at.isoformat() if hasattr(self.completed_at, 'isoformat') else self.completed_at
        
        # Handle datetime conversion to make JSON serializable
        for key, value in data.items():
            if isinstance(value, dict):
                # Convert any datetime objects in nested dictionaries
                for nested_key, nested_value in value.items():
                    if hasattr(nested_value, 'isoformat'):
                        value[nested_key] = nested_value.isoformat()
                        
        return data