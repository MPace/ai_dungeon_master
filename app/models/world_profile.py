"""
WorldProfile model for AI Dungeon Master
"""
import os
import yaml
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class WorldProfile:
    """WorldProfile model representing a game world and its rules"""
    
    # Path to the worlds directory
    WORLDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'worlds'))
    
    def __init__(self, world_id=None, name=None, vibe=None, 
                 forbidden_elements=None, common_elements=None, 
                 tone_guidelines=None):
        """
        Initialize a world profile
        
        Args:
            world_id (str): Unique ID for the world (e.g., "forgotten_realms")
            name (str): Display name of the world
            vibe (str): High-level description of the world's feel
            forbidden_elements (List[str]): Items, concepts, technologies disallowed
            common_elements (List[str]): Items, concepts expected in this world
            tone_guidelines (str): Instructions for the AI DM's narrative tone and style
        """
        self.world_id = world_id or ""
        self.name = name or ""
        self.vibe = vibe or ""
        self.forbidden_elements = forbidden_elements or []
        self.common_elements = common_elements or []
        self.tone_guidelines = tone_guidelines or ""
    
    @classmethod
    def from_dict(cls, data):
        """Create a WorldProfile instance from a dictionary"""
        if not data:
            return None
        
        return cls(
            world_id=data.get('world_id', data.get('id', '')),
            name=data.get('name', ''),
            vibe=data.get('vibe', ''),
            forbidden_elements=data.get('forbidden_elements', []),
            common_elements=data.get('common_elements', []),
            tone_guidelines=data.get('tone_guidelines', '')
        )
    
    def to_dict(self):
        """Convert WorldProfile instance to a dictionary"""
        return {
            'world_id': self.world_id,
            'name': self.name,
            'vibe': self.vibe,
            'forbidden_elements': self.forbidden_elements,
            'common_elements': self.common_elements,
            'tone_guidelines': self.tone_guidelines
        }
    
    def is_element_forbidden(self, element):
        """
        Check if an element is forbidden in this world
        
        Args:
            element (str): Element to check
            
        Returns:
            bool: True if the element is forbidden, False otherwise
        """
        # Case-insensitive check for forbidden elements
        element_lower = element.lower()
        return any(forbidden.lower() == element_lower for forbidden in self.forbidden_elements)
    
    def is_element_common(self, element):
        """
        Check if an element is common in this world
        
        Args:
            element (str): Element to check
            
        Returns:
            bool: True if the element is common, False otherwise
        """
        # Case-insensitive check for common elements
        element_lower = element.lower()
        return any(common.lower() == element_lower for common in self.common_elements)
    
    @classmethod
    def load(cls, world_id):
        """
        Load a world profile from a YAML file
        
        Args:
            world_id (str): ID of the world to load
            
        Returns:
            WorldProfile: World profile instance or None if not found
        """
        # Try both yaml and yml extensions
        for ext in ['.yaml', '.yml']:
            file_path = os.path.join(cls.WORLDS_DIR, f"{world_id}{ext}")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        world_data = yaml.safe_load(f)
                        
                        # Ensure world_id is set
                        if 'world_id' not in world_data:
                            world_data['world_id'] = world_id
                        
                        return cls.from_dict(world_data)
                except Exception as e:
                    logger.error(f"Error loading world profile from {file_path}: {e}")
                    return None
        
        logger.warning(f"World profile not found for ID: {world_id}")
        return None
    
    @classmethod
    def list_available_worlds(cls):
        """
        List all available world profiles
        
        Returns:
            List[Dict]: List of basic world information (id, name)
        """
        worlds = []
        
        if not os.path.exists(cls.WORLDS_DIR):
            logger.warning(f"Worlds directory not found: {cls.WORLDS_DIR}")
            return worlds
        
        for filename in os.listdir(cls.WORLDS_DIR):
            if filename.endswith(('.yaml', '.yml')):
                world_id = os.path.splitext(filename)[0]
                
                try:
                    world = cls.load(world_id)
                    if world:
                        worlds.append({
                            'id': world.world_id,
                            'name': world.name
                        })
                except Exception as e:
                    logger.error(f"Error loading world from {filename}: {e}")
        
        return worlds