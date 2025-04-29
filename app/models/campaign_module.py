"""
Campaign Module model for AI Dungeon Master
"""
import os
import yaml
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CampaignModule:
    """Model representing a campaign or adventure module with narrative structure"""
    
    # Path to the campaigns directory
    CAMPAIGNS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'campaigns'))
    
    def __init__(self, module_id=None, name=None, starting_info=None,
                 locations=None, npcs=None, quests=None, events=None,
                 world_id=None):
        """
        Initialize a campaign module
        
        Args:
            module_id (str): Unique ID for the campaign
            name (str): Campaign display name
            starting_info (str): Initial setup description
            locations (Dict): Map of location_id to location objects
            npcs (Dict): Map of npc_id to NPC objects
            quests (Dict): Map of quest_id to quest objects
            events (Dict): Map of event_id to event definitions
            world_id (str): ID of the world this campaign is set in
        """
        self.module_id = module_id or ""
        self.name = name or ""
        self.starting_info = starting_info or ""
        self.locations = locations or {}
        self.npcs = npcs or {}
        self.quests = quests or {}
        self.events = events or {}
        self.world_id = world_id or ""
    
    @classmethod
    def from_dict(cls, data):
        """Create a CampaignModule instance from a dictionary"""
        if not data:
            return None
        
        return cls(
            module_id=data.get('module_id', data.get('id', '')),
            name=data.get('name', ''),
            starting_info=data.get('starting_info', ''),
            locations=data.get('locations', {}),
            npcs=data.get('npcs', {}),
            quests=data.get('quests', {}),
            events=data.get('events', {}),
            world_id=data.get('world_id', '')
        )
    
    def to_dict(self):
        """Convert CampaignModule instance to a dictionary"""
        return {
            'module_id': self.module_id,
            'name': self.name,
            'starting_info': self.starting_info,
            'locations': self.locations,
            'npcs': self.npcs,
            'quests': self.quests,
            'events': self.events,
            'world_id': self.world_id
        }
    
    @classmethod
    def load(cls, module_id, world_id=None):
        """
        Load a campaign module from a YAML file
        
        Args:
            module_id (str): ID of the module to load
            world_id (str, optional): World ID to search in specific world folder
            
        Returns:
            CampaignModule: Campaign module instance or None if not found
        """
        # Determine where to look for the campaign file
        if world_id:
            # Look in world-specific directory first
            world_campaign_dir = os.path.join(cls.CAMPAIGNS_DIR, world_id)
            for ext in ['.yaml', '.yml']:
                file_path = os.path.join(world_campaign_dir, f"{module_id}{ext}")
                if os.path.exists(file_path):
                    return cls._load_from_file(file_path, module_id, world_id)
        
        # Look in the general campaigns directory
        for ext in ['.yaml', '.yml']:
            file_path = os.path.join(cls.CAMPAIGNS_DIR, f"{module_id}{ext}")
            if os.path.exists(file_path):
                return cls._load_from_file(file_path, module_id, world_id)
        
        logger.warning(f"Campaign module not found for ID: {module_id}")
        return None
    
    @classmethod
    def _load_from_file(cls, file_path, module_id, world_id=None):
        """
        Load a campaign module from a specific file path
        
        Args:
            file_path (str): Path to the YAML file
            module_id (str): ID of the module
            world_id (str, optional): ID of the world
            
        Returns:
            CampaignModule: Campaign module instance or None if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                module_data = yaml.safe_load(f)
                
                # Ensure module_id and world_id are set
                if 'module_id' not in module_data:
                    module_data['module_id'] = module_id
                
                if world_id and 'world_id' not in module_data:
                    module_data['world_id'] = world_id
                
                return cls.from_dict(module_data)
        except Exception as e:
            logger.error(f"Error loading campaign module from {file_path}: {e}")
            return None
    
    @classmethod
    def list_available_campaigns(cls, world_id=None):
        """
        List all available campaign modules, optionally filtered by world
        
        Args:
            world_id (str, optional): Filter by world ID
            
        Returns:
            List[Dict]: List of basic campaign information (id, name, world_id)
        """
        campaigns = []
        
        # Check if campaigns directory exists
        if not os.path.exists(cls.CAMPAIGNS_DIR):
            logger.warning(f"Campaigns directory not found: {cls.CAMPAIGNS_DIR}")
            return campaigns
        
        # If world_id is provided, check the world-specific folder first
        if world_id:
            world_campaign_dir = os.path.join(cls.CAMPAIGNS_DIR, world_id)
            if os.path.exists(world_campaign_dir) and os.path.isdir(world_campaign_dir):
                for filename in os.listdir(world_campaign_dir):
                    if filename.endswith(('.yaml', '.yml')):
                        campaign_id = os.path.splitext(filename)[0]
                        campaign = cls.load(campaign_id, world_id)
                        if campaign:
                            campaigns.append({
                                'id': campaign.module_id,
                                'name': campaign.name,
                                'world_id': campaign.world_id
                            })
        
        # Check main campaigns directory
        for filename in os.listdir(cls.CAMPAIGNS_DIR):
            # Skip world directories
            if os.path.isdir(os.path.join(cls.CAMPAIGNS_DIR, filename)):
                continue
                
            if filename.endswith(('.yaml', '.yml')):
                campaign_id = os.path.splitext(filename)[0]
                campaign = cls.load(campaign_id)
                
                # If filtering by world_id, skip campaigns for other worlds
                if world_id and campaign and campaign.world_id != world_id:
                    continue
                    
                if campaign:
                    campaigns.append({
                        'id': campaign.module_id,
                        'name': campaign.name,
                        'world_id': campaign.world_id
                    })
        
        return campaigns
    
    def get_location(self, location_id):
        """Get location data by ID"""
        return self.locations.get(location_id)
    
    def get_npc(self, npc_id):
        """Get NPC data by ID"""
        return self.npcs.get(npc_id)
    
    def get_quest(self, quest_id):
        """Get quest data by ID"""
        return self.quests.get(quest_id)
    
    def get_event(self, event_id):
        """Get event data by ID"""
        return self.events.get(event_id)
    
    def get_quest_stage(self, quest_id, stage_id):
        """Get a specific stage of a quest"""
        quest = self.get_quest(quest_id)
        if not quest or 'stages' not in quest:
            return None
            
        for stage in quest['stages']:
            if stage.get('stage_id') == stage_id:
                return stage
                
        return None