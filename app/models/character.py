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
        """Create a Character instance from a dictionary - handles React frontend format"""
        if not data:
            logger.warning("Empty data passed to Character.from_dict")
            return None
        
        try:
            # Create a working copy to avoid modifying the original
            working_data = data.copy()
            
            # Extract fields using a systematic approach to handle React data format
            extracted_data = {}
            
            # Extract name (could be 'name' or 'characterName')
            extracted_data['name'] = working_data.get('name') or working_data.get('characterName', '')
            
            # Extract race (could be 'race', 'raceName')
            extracted_data['race'] = working_data.get('race') or working_data.get('raceName', '')
            
            # Extract class (could be 'class', 'character_class', 'className')
            extracted_data['character_class'] = (
                working_data.get('class') or 
                working_data.get('character_class') or 
                working_data.get('className', '')
            )
            
            # Extract background (could be 'background', 'backgroundName')
            extracted_data['background'] = working_data.get('background') or working_data.get('backgroundName', '')
            
            # Extract character_id
            extracted_data['character_id'] = working_data.get('character_id') or working_data.get('characterId')
            if not extracted_data['character_id']:
                extracted_data['character_id'] = str(uuid.uuid4())
            
            # Extract user_id
            extracted_data['user_id'] = working_data.get('user_id')
            
            # Extract draft status
            extracted_data['is_draft'] = working_data.get('isDraft', False) if 'isDraft' in working_data else working_data.get('is_draft', False)
            
            # Extract level
            extracted_data['level'] = working_data.get('level', 1)
            
            # Extract description
            extracted_data['description'] = working_data.get('description', '')
            
            # Extract abilities from various possible locations
            if 'abilities' in working_data and working_data['abilities']:
                extracted_data['abilities'] = working_data['abilities']
            elif 'finalAbilityScores' in working_data and working_data['finalAbilityScores']:
                extracted_data['abilities'] = working_data['finalAbilityScores']
            else:
                extracted_data['abilities'] = {
                    'strength': 10,
                    'dexterity': 10,
                    'constitution': 10,
                    'intelligence': 10,
                    'wisdom': 10,
                    'charisma': 10
                }
            
            # Extract skills
            extracted_data['skills'] = []
            if 'skills' in working_data and isinstance(working_data['skills'], list):
                extracted_data['skills'] = working_data['skills']
            elif 'proficiencies' in working_data and isinstance(working_data['proficiencies'], dict):
                if 'skills' in working_data['proficiencies'] and isinstance(working_data['proficiencies']['skills'], list):
                    extracted_data['skills'] = working_data['proficiencies']['skills']
            
            # Extract equipment
            if 'equipment' in working_data and working_data['equipment']:
                extracted_data['equipment'] = working_data['equipment']
            else:
                extracted_data['equipment'] = {}
            
            # Extract features
            if 'features' in working_data and working_data['features']:
                extracted_data['features'] = working_data['features']
            elif 'classFeatures' in working_data and working_data['classFeatures']:
                extracted_data['features'] = working_data['classFeatures']
            else:
                extracted_data['features'] = {}
            
            # Extract spellcasting
            if 'spellcasting' in working_data and working_data['spellcasting']:
                extracted_data['spellcasting'] = working_data['spellcasting']
            elif 'spells' in working_data and working_data['spells']:
                extracted_data['spellcasting'] = working_data['spells']
            else:
                extracted_data['spellcasting'] = {}
            
            # Extract hit points - critically important for game interface
            if 'hitPoints' in working_data and working_data['hitPoints']:
                extracted_data['hit_points'] = working_data['hitPoints']
            elif 'hit_points' in working_data and working_data['hit_points']:
                extracted_data['hit_points'] = working_data['hit_points']
            elif 'calculatedStats' in working_data and working_data['calculatedStats'] and 'hitPoints' in working_data['calculatedStats']:
                # Extract from the calculated stats in React
                hp_value = working_data['calculatedStats']['hitPoints']
                extracted_data['hit_points'] = {
                    'current': hp_value,
                    'max': hp_value,
                    'hitDie': cls._get_hit_die_for_class(extracted_data['character_class'])
                }
            else:
                # Compute based on class and constitution if possible
                extracted_data['hit_points'] = cls._calculate_hit_points(
                    extracted_data['character_class'], 
                    extracted_data['abilities'].get('constitution', 10)
                )
            
            # Parse datetime fields
            for date_field in ['created_at', 'updated_at', 'last_played']:
                value = working_data.get(date_field)
                if isinstance(value, str):
                    try:
                        extracted_data[date_field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        extracted_data[date_field] = datetime.utcnow() if date_field != 'last_played' else None
                else:
                    extracted_data[date_field] = datetime.utcnow() if date_field != 'last_played' else None
            
            # Handle completed_at field
            completed_at = working_data.get('completedAt') or working_data.get('completed_at')
            if isinstance(completed_at, str):
                try:
                    extracted_data['completed_at'] = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                except ValueError:
                    extracted_data['completed_at'] = None if extracted_data['is_draft'] else datetime.utcnow()
            else:
                extracted_data['completed_at'] = None if extracted_data['is_draft'] else datetime.utcnow()
            
            # Handle _id field
            _id = working_data.get('_id')
            if isinstance(_id, ObjectId):
                extracted_data['_id'] = str(_id)
            else:
                extracted_data['_id'] = _id
            
            # Construct the character instance with extracted data
            return cls(
                name=extracted_data['name'],
                race=extracted_data['race'],
                character_class=extracted_data['character_class'],
                background=extracted_data['background'],
                level=extracted_data['level'],
                abilities=extracted_data['abilities'],
                skills=extracted_data['skills'],
                equipment=extracted_data['equipment'],
                features=extracted_data['features'],
                spellcasting=extracted_data['spellcasting'],
                hit_points=extracted_data['hit_points'],
                description=extracted_data['description'],
                user_id=extracted_data['user_id'],
                character_id=extracted_data['character_id'],
                created_at=extracted_data['created_at'],
                updated_at=extracted_data['updated_at'],
                last_played=extracted_data['last_played'],
                is_draft=extracted_data['is_draft'],
                completed_at=extracted_data['completed_at'],
                _id=extracted_data['_id']
            )
        except Exception as e:
            logger.error(f"Error in Character.from_dict: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    @classmethod
    def _get_hit_die_for_class(cls, character_class):
        """Get the appropriate hit die based on character class"""
        if not character_class:
            return 'd8'
            
        class_name = character_class.lower()
        
        if class_name == 'barbarian':
            return 'd12'
        elif class_name in ['fighter', 'paladin', 'ranger']:
            return 'd10'
        elif class_name in ['sorcerer', 'wizard']:
            return 'd6'
        else:
            return 'd8'  # Default for bard, cleric, druid, monk, rogue, warlock

    @classmethod
    def _calculate_hit_points(cls, character_class, constitution):
        """Calculate hit points based on class and constitution"""
        hit_die = cls._get_hit_die_for_class(character_class)
        
        # Get the die size
        die_size = int(hit_die[1:]) if hit_die and len(hit_die) > 1 else 8
        
        # At first level, characters get maximum hit die + constitution modifier
        constitution_modifier = (constitution - 10) // 2
        max_hp = die_size + constitution_modifier
        
        # Ensure minimum of 1 hit point
        max_hp = max(1, max_hp)
        
        return {
            'current': max_hp,
            'max': max_hp,
            'hitDie': hit_die
        }
    
    def to_dict(self):
        """Convert Character instance to a dictionary for JSON serialization with both formats"""
        # Base dictionary with standard attributes
        data = {
            'name': self.name,
            'characterName': self.name,  # Include React format
            'race': self.race,
            'raceName': self.race,  # Include React format
            'class': self.character_class,
            'character_class': self.character_class,
            'className': self.character_class,  # Include React format
            'background': self.background,
            'backgroundName': self.background,  # Include React format
            'level': self.level,
            'abilities': self.abilities,
            'finalAbilityScores': self.abilities,  # Include React format
            'skills': self.skills,
            'equipment': self.equipment,
            'features': self.features,
            'classFeatures': self.features,  # Include React format
            'spellcasting': self.spellcasting,
            'spells': self.spellcasting,  # Include React format
            'hit_points': self.hit_points,
            'hitPoints': self.hit_points,  # Include React format
            'description': self.description,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'characterId': self.character_id,  # Include React format
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at,
            'last_played': self.last_played.isoformat() if hasattr(self.last_played, 'isoformat') and self.last_played else None,
            'isDraft': self.is_draft,
            'is_draft': self.is_draft
        }
        
        # Add completed_at only if it exists
        if self.completed_at:
            data['completedAt'] = self.completed_at.isoformat() if hasattr(self.completed_at, 'isoformat') else self.completed_at
            data['completed_at'] = data['completedAt']
        
        # Handle datetime conversion to make JSON serializable
        for key, value in list(data.items()):
            if isinstance(value, dict):
                # Convert any datetime objects in nested dictionaries
                for nested_key, nested_value in list(value.items()):
                    if hasattr(nested_value, 'isoformat'):
                        value[nested_key] = nested_value.isoformat()
        
        return data