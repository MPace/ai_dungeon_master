"""
Character model with enhanced frontend-to-backend data mapping
"""
from datetime import datetime
import uuid
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)


class Character:
    """Character model representing a player character"""
    
    def __init__(self, name, race, character_class, background, level=1,
                 abilities=None, skills=None, equipment=None, features=None,
                 spellcasting=None, hit_points=None, description=None,
                 user_id=None, character_id=None, created_at=None, 
                 updated_at=None, last_played=None, is_draft=False, 
                 completed_at=None, _id=None, alignment=None):
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
        self.alignment = alignment
    
    @classmethod
    def from_dict(cls, data):
        """Create a Character instance from a dictionary (handles both camelCase and snake_case)"""
        if data is None:
            logger.warning("None data passed to Character.from_dict")
            return None
        
        try:
            # First check for required fields - try both camelCase and snake_case variants
            name = data.get('name') or data.get('characterName') or ""
            if not name and 'characterName' not in data and 'name' not in data:
                logger.warning("Character data missing 'name'/'characterName' field")
                
            # Handle 'character_id' being missing or None
            character_id = data.get('character_id') or data.get('characterId')
            if not character_id:
                character_id = str(uuid.uuid4())
                logger.info(f"Generated missing character_id: {character_id}")
            
            # Convert _id from ObjectId to string if present
            _id = data.get('_id')
            if isinstance(_id, ObjectId):
                _id = str(_id)
            
            # Map class field (handle different naming conventions)
            character_class = (
                data.get('class') or 
                data.get('character_class') or 
                data.get('className') or
                ""
            )
            
            # Map race field
            race = data.get('race') or data.get('raceName') or ""
            
            # Map background field
            background = data.get('background') or data.get('backgroundName') or ""
            
            # Map isDraft to is_draft
            is_draft = data.get('isDraft', False) if 'isDraft' in data else data.get('is_draft', False)
            
            # Map abilities (could be in finalAbilityScores, baseAbilityScores, or abilities)
            abilities = (
                data.get('abilities') or 
                data.get('finalAbilityScores') or
                {}
            )
            
            # Map skills field
            skills = []
            # Check for skills in the nested proficiencies object first (React format)
            if 'proficiencies' in data and isinstance(data['proficiencies'], dict):
                if 'skills' in data['proficiencies'] and isinstance(data['proficiencies']['skills'], list):
                    skills = data['proficiencies']['skills']
            # Then check direct skills field (API format)
            elif 'skills' in data and isinstance(data['skills'], list):
                skills = data['skills']
            
            # Map description
            description = data.get('description') or ""
            
            # Parse datetime fields
            created_at = data.get('created_at') or data.get('createdAt')
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except ValueError:
                    created_at = datetime.utcnow()
            elif not created_at:
                created_at = datetime.utcnow()
                
            updated_at = data.get('updated_at') or data.get('updatedAt')
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except ValueError:
                    updated_at = datetime.utcnow()
            elif not updated_at:
                updated_at = datetime.utcnow()
                
            last_played = data.get('last_played') or data.get('lastPlayed')
            if isinstance(last_played, str):
                try:
                    last_played = datetime.fromisoformat(last_played.replace('Z', '+00:00'))
                except ValueError:
                    last_played = None
                    
            completed_at = data.get('completedAt') or data.get('completed_at')
            if isinstance(completed_at, str):
                try:
                    completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                except ValueError:
                    completed_at = None if is_draft else datetime.utcnow()
            elif not completed_at and not is_draft:
                completed_at = datetime.utcnow()
            
            # Map hitPoints to hit_points - try multiple formats
            hit_points = data.get('hitPoints') or data.get('hit_points') or data.get('calculatedStats', {}).get('hitPoints') or {}
            
            # Map equipment field - handle nested structure
            equipment = data.get('equipment', {})
            
            # Map features field - try both camelCase and snake_case
            features = data.get('features') or data.get('classFeatures') or {}
            
            # Map spellcasting field
            spellcasting = data.get('spellcasting') or data.get('spells') or {}
            
            # Map level field
            level = data.get('level', 1)
            
            # Map alignment field
            alignment = data.get('alignment') or data.get('alignmentName')
                
            # Construct the character instance
            return cls(
                name=name,
                race=race,
                character_class=character_class,
                background=background,
                level=level,
                abilities=abilities,
                skills=skills,
                equipment=equipment,
                features=features,
                spellcasting=spellcasting,
                hit_points=hit_points,
                description=description,
                user_id=data.get('user_id'),
                character_id=character_id,
                created_at=created_at,
                updated_at=updated_at,
                last_played=last_played,
                is_draft=is_draft,
                completed_at=completed_at,
                _id=_id,
                alignment=alignment
            )
        except Exception as e:
            logger.error(f"Error in Character.from_dict: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def to_dict(self):
        """Convert Character instance to a dictionary for JSON serialization
        with both snake_case and camelCase keys for compatibility"""
        # First get the base dictionary with standard attributes
        data = {
            'name': self.name,
            'race': self.race,
            'class': self.character_class,  # Use 'class' key for frontend compatibility
            'character_class': self.character_class,  # Include both for backend compatibility
            'background': self.background,
            'level': self.level,
            'abilities': self.abilities,
            'skills': self.skills,
            'equipment': self.equipment,
            'features': self.features,
            'spellcasting': self.spellcasting,
            'hitPoints': self.hit_points,  # Use 'hitPoints' for frontend compatibility
            'hit_points': self.hit_points,  # Include both for backend compatibility
            'description': self.description,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at,
            'last_played': self.last_played.isoformat() if hasattr(self.last_played, 'isoformat') and self.last_played else None,
            'isDraft': self.is_draft,  # Use 'isDraft' for frontend compatibility
            'is_draft': self.is_draft,  # Include both for backend compatibility
        }
        
        # Add alignment if it exists
        if self.alignment:
            data['alignment'] = self.alignment
        
        # Add completed_at only if it exists
        if self.completed_at:
            data['completedAt'] = self.completed_at.isoformat() if hasattr(self.completed_at, 'isoformat') else self.completed_at
            data['completed_at'] = data['completedAt']  # Include both for backend compatibility
        
        # Handle datetime conversion to make JSON serializable
        for key, value in data.items():
            if isinstance(value, dict):
                # Convert any datetime objects in nested dictionaries
                for nested_key, nested_value in value.items():
                    if hasattr(nested_value, 'isoformat'):
                        value[nested_key] = nested_value.isoformat()
                        
        # Add additional frontend-compatible fields for React
        data['characterName'] = self.name
        data['className'] = self.character_class
        data['raceName'] = self.race
        data['backgroundName'] = self.background
        
        return data