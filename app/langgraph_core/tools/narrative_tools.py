# app/langgraph_core/tools/narrative_tools.py
"""
Narrative Tools for AI Dungeon Master

These tools implement narrative and time management functionality for the game.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import re

from app.extensions import get_db
from app.models.campaign_module import CampaignModule
from app.langgraph_core.state import AIGameState, TrackedNarrativeState

logger = logging.getLogger(__name__)

class NarrativeTriggerEvaluatorTool:
    """Tool for evaluating narrative triggers based on game state"""
    
    def __init__(self):
        """Initialize the narrative trigger evaluator"""
        self.db = get_db()
    
    def evaluate_triggers(self, state: AIGameState) -> List[Dict[str, Any]]:
        """
        Evaluate if any narrative triggers are met based on the current state
        
        Args:
            state: Current game state
            
        Returns:
            List of triggered events with their outcomes
        """
        try:
            # Extract necessary state information
            player_input = state.get("player_input", "")
            intent_data = state.get("intent_data", {})
            narrative_state = state.get("tracked_narrative_state", {})
            current_location = state.get("current_location_id")
            campaign_module_id = state.get("campaign_module_id")
            
            # Get list of fired events
            global_flags = narrative_state.get("global_flags", [])
            fired_events = [flag for flag in global_flags if flag.startswith("event_fired_")]
            
            # If no campaign module, no triggers to evaluate
            if not campaign_module_id:
                logger.info("No campaign module specified, skipping trigger evaluation")
                return []
            
            # Get relevant events from the campaign module
            events = self._get_campaign_events(campaign_module_id, current_location)
            
            # Check each event against the current state
            triggered_events = []
            
            for event in events:
                # Skip events that have already fired if they're marked as first_time
                event_id = event.get("id", "unknown")
                if event.get("first_time", False) and f"event_fired_{event_id}" in fired_events:
                    continue
                
                # Check if trigger conditions are met
                trigger_type = event.get("trigger_type", "")
                conditions = event.get("conditions", {})
                
                if self._check_trigger_conditions(
                    trigger_type=trigger_type,
                    conditions=conditions,
                    state=state
                ):
                    # Event is triggered
                    triggered_events.append(event)
                    logger.info(f"Event triggered: {event_id}")
            
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error evaluating narrative triggers: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _get_campaign_events(self, campaign_module_id: str,
                      current_location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relevant events from the campaign module
        
        Args:
            campaign_module_id: ID of the campaign module
            current_location: Current location ID
            
        Returns:
            List of event definitions
        """
        # Load campaign module
        campaign_module = CampaignModule.load(campaign_module_id)
        
        if not campaign_module:
            logger.warning(f"Campaign module not found: {campaign_module_id}")
            return []
        
        # Get all events from the module
        all_events = []
        
        # Location-specific events
        if current_location and current_location in campaign_module.locations:
            location = campaign_module.locations[current_location]
            location_events = location.get("events", [])
            all_events.extend(location_events)
        
        # Global events
        if hasattr(campaign_module, 'events') and campaign_module.events:
            # Convert to list if it's a dict
            if isinstance(campaign_module.events, dict):
                global_events = list(campaign_module.events.values())
            else:
                global_events = campaign_module.events
            
            all_events.extend(global_events)
        
        # Quest-related events
        if hasattr(campaign_module, 'quests') and campaign_module.quests:
            for quest_id, quest in campaign_module.quests.items():
                if isinstance(quest, dict) and "stages" in quest:
                    for stage in quest["stages"]:
                        if "events" in stage:
                            all_events.extend(stage["events"])
        
        # NPC-related events for NPCs in the current location
        if current_location and hasattr(campaign_module, 'npcs') and campaign_module.npcs:
            location_data = campaign_module.get_location(current_location)
            if location_data and "npcs_present" in location_data:
                for npc_id in location_data["npcs_present"]:
                    npc = campaign_module.get_npc(npc_id)
                    if npc and "dialogue_triggers" in npc:
                        all_events.extend(npc["dialogue_triggers"])
        
        return all_events
    
    def _check_trigger_conditions(self, trigger_type: str, conditions: Dict[str, Any],
                           state: AIGameState) -> bool:
        """
        Check if trigger conditions are met
        
        Args:
            trigger_type: Type of trigger
            conditions: Trigger conditions
            state: Current game state
            
        Returns:
            bool: True if conditions are met
        """
        # Extract necessary state information
        player_input = state.get("player_input", "").lower()
        intent_data = state.get("intent_data", {})
        narrative_state = state.get("tracked_narrative_state", {})
        current_location = state.get("current_location_id")
        environment_state = narrative_state.get("environment_state", {})
        
        # Check based on trigger type
        if trigger_type == "enter_location":
            required_location = conditions.get("location_id")
            return required_location == current_location
            
        elif trigger_type == "speak_to_npc":
            npc_id = conditions.get("npc_id")
            keywords = conditions.get("keywords", [])
            
            # Check if the NPC is present in the current location
            npc_present = self._is_npc_present(npc_id, current_location, state)
            if not npc_present:
                return False
            
            # Check if NPC is mentioned in player input
            npc_name = self._get_npc_name(npc_id, state)
            if not npc_name or npc_name.lower() not in player_input:
                return False
            
            # Check for specific keywords if provided
            if keywords:
                return any(keyword.lower() in player_input for keyword in keywords)
            
            return True
            
        elif trigger_type == "use_item_on_target":
            item_id = conditions.get("item_id")
            target_id = conditions.get("target_id")
            
            # Check if the player has the item
            has_item = self._player_has_item(item_id, state)
            if not has_item:
                return False
            
            # Check intent and slots
            if intent_data.get("intent") == "use_item":
                item_name = intent_data.get("slots", {}).get("item_name", "").lower()
                
                # Check if item matches
                item_name_from_id = self._get_item_name(item_id, state)
                if not item_name_from_id or item_name_from_id.lower() not in item_name:
                    return False
                
                # Check if target is mentioned in player input
                target_name = self._get_entity_name(target_id, state)
                if not target_name or target_name.lower() not in player_input:
                    return False
                
                return True
            
            return False
            
        elif trigger_type == "quest_stage_reached":
            quest_id = conditions.get("quest_id")
            stage_id = conditions.get("stage_id")
            
            # Check quest status
            quest_status = narrative_state.get("quest_status", {})
            return quest_status.get(quest_id) == stage_id
            
        elif trigger_type == "flag_set":
            required_flags = conditions.get("required_flags", [])
            global_flags = narrative_state.get("global_flags", [])
            
            # Check if all required flags are set
            return all(flag in global_flags for flag in required_flags)
            
        elif trigger_type == "time_based":
            time_condition = conditions.get("time_condition", {})
            current_day_phase = environment_state.get("current_day_phase")
            
            # Check day phase condition
            if "day_phase" in time_condition and current_day_phase:
                if time_condition["day_phase"] != current_day_phase:
                    return False
            
            # Check specific time range if provided
            if "time_range" in time_condition:
                time_range = time_condition["time_range"]
                current_datetime_str = environment_state.get("current_datetime")
                
                if current_datetime_str:
                    try:
                        current_datetime = datetime.fromisoformat(current_datetime_str)
                        current_hour = current_datetime.hour
                        
                        start_hour = time_range.get("start", 0)
                        end_hour = time_range.get("end", 23)
                        
                        # Check if current hour is within range
                        if not (start_hour <= current_hour <= end_hour):
                            return False
                    except ValueError:
                        return False
            
            # Check specific date if provided
            if "specific_date" in time_condition:
                specific_date = time_condition["specific_date"]
                current_datetime_str = environment_state.get("current_datetime")
                
                if current_datetime_str:
                    try:
                        current_datetime = datetime.fromisoformat(current_datetime_str)
                        
                        year_match = specific_date.get("year") is None or specific_date.get("year") == current_datetime.year
                        month_match = specific_date.get("month") is None or specific_date.get("month") == current_datetime.month
                        day_match = specific_date.get("day") is None or specific_date.get("day") == current_datetime.day
                        
                        if not (year_match and month_match and day_match):
                            return False
                    except ValueError:
                        return False
            
            # If we've passed all time checks, the condition is met
            return True
            
        elif trigger_type == "inventory_change":
            # Check if player has acquired or lost a specific item
            item_id = conditions.get("item_id")
            action = conditions.get("action", "acquire")  # "acquire" or "lose"
            
            has_item = self._player_has_item(item_id, state)
            
            if action == "acquire":
                return has_item
            else:  # action == "lose"
                return not has_item
            
        elif trigger_type == "combat_start":
            # Check if combat has just started
            return state.get("game_state") == "combat"
            
        elif trigger_type == "combat_end":
            # Check if combat has just ended
            previous_state = state.get("previous_game_state")
            current_state = state.get("game_state")
            
            return previous_state == "combat" and current_state != "combat"
            
        elif trigger_type == "health_threshold":
            # Check if character health is below/above a threshold
            threshold = conditions.get("threshold", 0.5)  # Default to 50% health
            comparison = conditions.get("comparison", "below")  # "below" or "above"
            
            character_id = state.get("current_character_id")
            if not character_id:
                return False
            
            # Get character health data
            character_data = self._get_character_data(character_id)
            if not character_data:
                return False
            
            hit_points = character_data.get("hit_points", {})
            current_hp = hit_points.get("current", 0)
            max_hp = hit_points.get("max", 1)
            
            # Calculate health percentage
            health_percentage = current_hp / max_hp if max_hp > 0 else 0
            
            if comparison == "below":
                return health_percentage < threshold
            else:  # comparison == "above"
                return health_percentage > threshold
            
        elif trigger_type == "keyword_in_input":
            # Check if specific keywords are in player input
            keywords = conditions.get("keywords", [])
            match_all = conditions.get("match_all", False)
            
            if match_all:
                return all(keyword.lower() in player_input for keyword in keywords)
            else:
                return any(keyword.lower() in player_input for keyword in keywords)
        
        # Default case - unrecognized trigger type
        logger.warning(f"Unrecognized trigger type: {trigger_type}")
        return False
    
    def _is_npc_present(self, npc_id: str, location_id: str, state: AIGameState) -> bool:
        """
        Check if an NPC is present in the current location
        
        Args:
            npc_id: NPC identifier
            location_id: Current location identifier
            state: Current game state
            
        Returns:
            bool: True if the NPC is present
        """
        if not location_id:
            return False
        
        campaign_module_id = state.get("campaign_module_id")
        if not campaign_module_id:
            return False
        
        # Load campaign module
        campaign_module = CampaignModule.load(campaign_module_id)
        if not campaign_module:
            return False
        
        # Get location data
        location = campaign_module.get_location(location_id)
        if not location:
            return False
        
        # Check if NPC is in the location's NPC list
        npcs_present = location.get("npcs_present", [])
        
        # Handle both list of IDs and list of objects
        for npc in npcs_present:
            if isinstance(npc, dict) and npc.get("id") == npc_id:
                return True
            elif isinstance(npc, str) and npc == npc_id:
                return True
        
        # Check narrative state for dynamic NPC presence
        narrative_state = state.get("tracked_narrative_state", {})
        location_states = narrative_state.get("location_states", {})
        
        if location_id in location_states:
            location_state = location_states[location_id]
            
            # Check for "npcs_present" key in location state
            dynamic_npcs = location_state.get("npcs_present", [])
            
            for npc in dynamic_npcs:
                if isinstance(npc, dict) and npc.get("id") == npc_id:
                    return True
                elif isinstance(npc, str) and npc == npc_id:
                    return True
        
        return False

    def _player_has_item(self, item_id: str, state: AIGameState) -> bool:
        """
        Check if the player has a specific item in their inventory
        
        Args:
            item_id: Item identifier
            state: Current game state
            
        Returns:
            bool: True if the player has the item
        """
        character_id = state.get("current_character_id")
        if not character_id:
            return False
        
        # Get character data
        character_data = self._get_character_data(character_id)
        if not character_data:
            return False
        
        # Check equipment and inventory
        equipment = character_data.get("equipment", {})
        
        # Check inventory
        inventory = equipment.get("inventory", [])
        for item in inventory:
            if isinstance(item, dict) and (
                item.get("id") == item_id or 
                item.get("item_id") == item_id
            ):
                # Check quantity
                quantity = item.get("quantity", 1)
                return quantity > 0
        
        # Check equipped items in specific slots
        item_slots = ["weapon", "armor", "shield", "head", "neck", "cloak", 
                    "hands", "feet", "ring1", "ring2", "belt", "trinket"]
                    
        for slot in item_slots:
            if slot in equipment:
                equipped_item = equipment[slot]
                if isinstance(equipped_item, dict) and (
                    equipped_item.get("id") == item_id or
                    equipped_item.get("item_id") == item_id
                ):
                    return True
        
        return False

    def _get_character_data(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Get character data from database
        
        Args:
            character_id: Character identifier
            
        Returns:
            Dict or None: Character data if found
        """
        if not self.db:
            return None
        
        try:
            # Query for character
            character_doc = self.db.characters.find_one({"character_id": character_id})
            
            if not character_doc:
                return None
            
            # Convert to dict if it's an object
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
        
        except Exception as e:
            logger.error(f"Error getting character data: {e}")
            return None

    def _get_npc_name(self, npc_id: str, state: AIGameState) -> Optional[str]:
        """
        Get NPC name from ID
        
        Args:
            npc_id: NPC identifier
            state: Current game state
            
        Returns:
            NPC name or None if not found
        """
        campaign_module_id = state.get("campaign_module_id")
        if not campaign_module_id:
            return None
        
        # Load campaign module
        campaign_module = CampaignModule.load(campaign_module_id)
        
        if not campaign_module or not hasattr(campaign_module, 'npcs'):
            return None
        
        # Get NPC data
        npc = campaign_module.get_npc(npc_id)
        if npc and "name" in npc:
            return npc["name"]
        
        # Check if NPC is in the database
        if self.db:
            npc_doc = self.db.npcs.find_one({"npc_id": npc_id})
            if npc_doc and "name" in npc_doc:
                return npc_doc["name"]
        
        return None
    
    def _get_item_name(self, item_id: str, state: AIGameState) -> Optional[str]:
        """
        Get item name from ID
        
        Args:
            item_id: Item identifier
            state: Current game state
            
        Returns:
            Item name or None if not found
        """
        campaign_module_id = state.get("campaign_module_id")
        if not campaign_module_id:
            return None
        
        # Load campaign module
        campaign_module = CampaignModule.load(campaign_module_id)
        
        if not campaign_module:
            return None
        
        # Check various item collections in the module
        item_collections = ["items", "weapons", "armor", "treasures"]
        
        for collection_name in item_collections:
            if hasattr(campaign_module, collection_name):
                collection = getattr(campaign_module, collection_name)
                if item_id in collection:
                    item = collection[item_id]
                    if isinstance(item, dict) and "name" in item:
                        return item["name"]
        
        # Check locations for items
        if hasattr(campaign_module, 'locations'):
            for location_id, location in campaign_module.locations.items():
                if isinstance(location, dict) and "items_present" in location:
                    for item in location["items_present"]:
                        if isinstance(item, dict) and item.get("id") == item_id:
                            return item.get("name")
        
        # Check database
        if self.db:
            item_doc = self.db.items.find_one({"item_id": item_id})
            if item_doc and "name" in item_doc:
                return item_doc["name"]
        
        return None
    
    def _get_entity_name(self, entity_id: str, state: AIGameState) -> Optional[str]:
        """
        Get entity name from ID (could be NPC, location, item, etc.)
        
        Args:
            entity_id: Entity identifier
            state: Current game state
            
        Returns:
            Entity name or None if not found
        """
        # First try as NPC
        npc_name = self._get_npc_name(entity_id, state)
        if npc_name:
            return npc_name
        
        # Then try as item
        item_name = self._get_item_name(entity_id, state)
        if item_name:
            return item_name
        
        # Try as location
        campaign_module_id = state.get("campaign_module_id")
        if campaign_module_id:
            campaign_module = CampaignModule.load(campaign_module_id)
            if campaign_module and hasattr(campaign_module, 'locations'):
                location = campaign_module.get_location(entity_id)
                if location and "name" in location:
                    return location["name"]
        
        # Try as quest
        if campaign_module_id:
            campaign_module = CampaignModule.load(campaign_module_id)
            if campaign_module and hasattr(campaign_module, 'quests'):
                quest = campaign_module.get_quest(entity_id)
                if quest and "name" in quest:
                    return quest["name"]
        
        # Check database for any entity
        if self.db:
            # Try different collections
            collections = ["npcs", "items", "locations", "quests"]
            for collection_name in collections:
                collection = getattr(self.db, collection_name, None)
                if collection:
                    entity_doc = collection.find_one({f"{collection_name[:-1]}_id": entity_id})
                    if entity_doc and "name" in entity_doc:
                        return entity_doc["name"]
        
        return None


class AdvanceTimeTool:
    """Tool for advancing game time"""
    
    def __init__(self):
        """Initialize time advancement tool"""
        pass
    
    def advance_time(self, state: AIGameState, duration: timedelta,
                  action_type: str, distance: Optional[float] = None) -> None:
        """
        Advance the game time by a specified duration
        
        Args:
            state: Current game state
            duration: Time to advance
            action_type: Type of action causing time advancement
            distance: Distance traveled (if applicable)
        """
        try:
            # Get environment state from narrative state
            narrative_state = state.get("tracked_narrative_state", {})
            
            if "environment_state" not in narrative_state:
                narrative_state["environment_state"] = {}
            
            environment_state = narrative_state["environment_state"]
            
            # Get current datetime
            current_datetime_str = environment_state.get("current_datetime")
            
            if current_datetime_str:
                try:
                    current_datetime = datetime.fromisoformat(current_datetime_str)
                except ValueError:
                    # If the datetime string is invalid, use current time
                    current_datetime = datetime.utcnow()
            else:
                # If no datetime is set, use current time
                current_datetime = datetime.utcnow()
            
            # Advance time
            new_datetime = current_datetime + duration
            
            # Update environment state
            environment_state["current_datetime"] = new_datetime.isoformat()
            
            # Update day phase
            environment_state["current_day_phase"] = self._calculate_day_phase(new_datetime)
            
            # Update the narrative state
            narrative_state["environment_state"] = environment_state
            state["tracked_narrative_state"] = narrative_state
            
            logger.info(f"Advanced time by {duration} for action: {action_type}")
            
        except Exception as e:
            logger.error(f"Error advancing time: {e}")
    
    def _calculate_day_phase(self, current_datetime: datetime) -> str:
        """
        Calculate the current phase of the day based on time
        
        Args:
            current_datetime: Current date and time
            
        Returns:
            str: Day phase (Morning, Afternoon, Evening, Night)
        """
        hour = current_datetime.hour
        
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"


class CalculateTravelTimeTool:
    """Tool for calculating travel time based on distance and mode"""
    
    def __init__(self):
        """Initialize travel time calculator"""
        pass
    
    def calculate_travel_time(self, state: AIGameState, distance: float,
                           travel_mode: str = "walk") -> timedelta:
        """
        Calculate time required for travel
        
        Args:
            state: Current game state
            distance: Distance to travel in miles
            travel_mode: Mode of travel (walk, horse, etc.)
            
        Returns:
            timedelta: Time required for travel
        """
        try:
            # Get character data for potential modifiers
            character_id = state.get("current_character_id")
            character_data = None
            
            if character_id:
                db = get_db()
                if db is not None:
                    character_doc = db.characters.find_one({"character_id": character_id})
                    if character_doc:
                        if hasattr(character_doc, 'to_dict'):
                            character_data = character_doc.to_dict()
                        else:
                            character_data = character_doc
            
            # Base travel speeds (miles per hour)
            travel_speeds = {
                "walk": 3.0,      # Normal walking speed
                "hike": 2.0,      # Challenging terrain
                "run": 6.0,       # Running
                "horse": 8.0,     # Horseback
                "wagon": 4.0,     # Wagon or cart
                "boat": 5.0,      # Riverboat
                "ship": 10.0,     # Sailing ship
                "swim": 1.0       # Swimming
            }
            
            # Get speed for travel mode
            speed = travel_speeds.get(travel_mode.lower(), 3.0)  # Default to walking
            
            # Apply character modifiers if applicable
            if character_data:
                # Example: Apply speed bonuses from character traits
                # This would be expanded in a real implementation
                pass
            
            # Calculate travel time in hours
            travel_hours = distance / speed
            
            # Convert to timedelta
            travel_time = timedelta(hours=travel_hours)
            
            return travel_time
            
        except Exception as e:
            logger.error(f"Error calculating travel time: {e}")
            # Default to a reasonable time if calculation fails
            return timedelta(hours=1)


class UpdateQuestStatusTool:
    """Tool for updating quest status in the narrative state"""
    
    def __init__(self):
        """Initialize quest status updater"""
        pass
    
    def update_quest_status(self, state: AIGameState, quest_id: str,
                         stage_id: str) -> None:
        """
        Update the status of a quest
        
        Args:
            state: Current game state
            quest_id: ID of the quest
            stage_id: New stage ID or 'completed'/'failed'
        """
        try:
            # Get narrative state
            narrative_state = state.get("tracked_narrative_state", {})
            
            if "quest_status" not in narrative_state:
                narrative_state["quest_status"] = {}
            
            # Update quest status
            narrative_state["quest_status"][quest_id] = stage_id
            
            # Update the narrative state
            state["tracked_narrative_state"] = narrative_state
            
            logger.info(f"Updated quest {quest_id} to stage {stage_id}")
            
        except Exception as e:
            logger.error(f"Error updating quest status: {e}")


class SetGlobalFlagTool:
    """Tool for setting global flags in the narrative state"""
    
    def __init__(self):
        """Initialize global flag setter"""
        pass
    
    def set_global_flag(self, state: AIGameState, flag_name: str,
                      value: bool = True) -> None:
        """
        Set or clear a global flag
        
        Args:
            state: Current game state
            flag_name: Name of the flag
            value: Flag value (True to set, False to clear)
        """
        try:
            # Get narrative state
            narrative_state = state.get("tracked_narrative_state", {})
            
            if "global_flags" not in narrative_state:
                narrative_state["global_flags"] = []
            
            # Set or clear flag
            if value:
                # Add flag if not already present
                if flag_name not in narrative_state["global_flags"]:
                    narrative_state["global_flags"].append(flag_name)
            else:
                # Remove flag if present
                if flag_name in narrative_state["global_flags"]:
                    narrative_state["global_flags"].remove(flag_name)
            
            # Update the narrative state
            state["tracked_narrative_state"] = narrative_state
            
            logger.info(f"{'Set' if value else 'Cleared'} global flag: {flag_name}")
            
        except Exception as e:
            logger.error(f"Error setting global flag: {e}")


class SetAreaFlagTool:
    """Tool for setting area-specific flags"""
    
    def __init__(self):
        """Initialize area flag setter"""
        pass
    
    def set_area_flag(self, state: AIGameState, location_id_or_region: str,
                    flag_name: str, value: bool = True) -> None:
        """
        Set or clear an environmental flag for a location or region
        
        Args:
            state: Current game state
            location_id_or_region: ID of the location or name of the region
            flag_name: Name of the flag
            value: Flag value
        """
        try:
            # Get environment state from narrative state
            narrative_state = state.get("tracked_narrative_state", {})
            
            if "environment_state" not in narrative_state:
                narrative_state["environment_state"] = {}
            
            environment_state = narrative_state["environment_state"]
            
            if "area_flags" not in environment_state:
                environment_state["area_flags"] = {}
            
            # Ensure the location has an entry
            if location_id_or_region not in environment_state["area_flags"]:
                environment_state["area_flags"][location_id_or_region] = []
            
            # Set or clear the flag
            area_flags = environment_state["area_flags"][location_id_or_region]
            
            if value:
                # Add flag if not already present
                if flag_name not in area_flags:
                    area_flags.append(flag_name)
            else:
                # Remove flag if present
                if flag_name in area_flags:
                    area_flags.remove(flag_name)
            
            # Update the environment state
            environment_state["area_flags"][location_id_or_region] = area_flags
            narrative_state["environment_state"] = environment_state
            state["tracked_narrative_state"] = narrative_state
            
            logger.info(f"{'Set' if value else 'Cleared'} area flag: {flag_name} for {location_id_or_region}")
            
        except Exception as e:
            logger.error(f"Error setting area flag: {e}")


class GetNarrativeContextTool:
    """Tool for retrieving narrative context for AI DM prompts"""
    
    def __init__(self):
        """Initialize narrative context getter"""
        self.db = get_db()
    
    def get_narrative_context(self, state: AIGameState) -> Dict[str, Any]:
        """
        Fetch relevant narrative context for the AI DM prompt
        
        Args:
            state: Current game state
            
        Returns:
            Dict with narrative context information
        """
        try:
            # Extract relevant state information
            narrative_state = state.get("tracked_narrative_state", {})
            current_location_id = state.get("current_location_id")
            campaign_module_id = state.get("campaign_module_id")
            
            # Initialize context
            context = {
                "location_description": None,
                "active_quests": [],
                "current_time": None,
                "environmental_conditions": []
            }
            
            # Get location description
            if current_location_id and campaign_module_id:
                location_desc = self._get_location_description(
                    campaign_module_id, current_location_id)
                context["location_description"] = location_desc
            
            # Get active quests
            quest_status = narrative_state.get("quest_status", {})
            for quest_id, stage_id in quest_status.items():
                if stage_id != "completed" and stage_id != "failed":
                    quest_info = self._get_quest_info(campaign_module_id, quest_id, stage_id)
                    if quest_info:
                        context["active_quests"].append(quest_info)
            
            # Get current time information
            environment_state = narrative_state.get("environment_state", {})
            current_datetime = environment_state.get("current_datetime")
            current_day_phase = environment_state.get("current_day_phase")
            
            if current_datetime:
                try:
                    dt = datetime.fromisoformat(current_datetime)
                    time_str = dt.strftime("%A, %B %d at %I:%M %p")
                    context["current_time"] = {
                        "datetime": time_str,
                        "day_phase": current_day_phase
                    }
                except ValueError:
                    pass
            
            # Get environmental conditions
            area_flags = environment_state.get("area_flags", {})
            
            # Current location conditions
            if current_location_id and current_location_id in area_flags:
                for flag in area_flags[current_location_id]:
                    condition = self._format_condition_from_flag(flag, current_location_id)
                    if condition:
                        context["environmental_conditions"].append(condition)
            
            # Global or regional conditions
            for region, flags in area_flags.items():
                if region != current_location_id and region in ["Wilderness", "Global"]:
                    for flag in flags:
                        condition = self._format_condition_from_flag(flag, region)
                        if condition:
                            context["environmental_conditions"].append(condition)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting narrative context: {e}")
            return {
                "location_description": None,
                "active_quests": [],
                "current_time": None,
                "environmental_conditions": []
            }
    
    def _get_location_description(self, campaign_module_id: str,
                               location_id: str) -> Optional[str]:
        """Get location description from campaign module"""
        # Load campaign module
        campaign_module = CampaignModule.load(campaign_module_id)
        
        if campaign_module and location_id in campaign_module.locations:
            location = campaign_module.locations[location_id]
            return location.get("description")
        
        return None
    
    def _get_quest_info(self, campaign_module_id: str, quest_id: str,
                      stage_id: str) -> Optional[Dict[str, str]]:
        """Get quest information from campaign module"""
        # Load campaign module
        campaign_module = CampaignModule.load(campaign_module_id)
        
        if campaign_module and quest_id in campaign_module.quests:
            quest = campaign_module.quests[quest_id]
            quest_name = quest.get("name", "Unknown Quest")
            
            # Find the current stage
            for stage in quest.get("stages", []):
                if stage.get("stage_id") == stage_id:
                    return {
                        "name": quest_name,
                        "objective": stage.get("objective", "")
                    }
        
        return None
    
    def _format_condition_from_flag(self, flag: str, location: str) -> Optional[str]:
        """Format environmental condition text from a flag"""
        # Map common flags to readable descriptions
        condition_map = {
            "foggy": "Fog covers the area",
            "raining": "It's raining",
            "snowing": "Snow is falling",
            "windy": "Strong winds blow through the area",
            "stormy": "A storm rages",
            "dark": "It's unusually dark",
            "bright": "Bright light illuminates the area",
            "cold": "It's bitterly cold",
            "hot": "It's oppressively hot",
            "quiet": "An eerie silence hangs in the air",
            "noisy": "The area is filled with noise",
            "crowded": "The place is crowded with people",
            "deserted": "The area is deserted"
        }
        
        # Check for known conditions
        if flag in condition_map:
            if location == "Global":
                return condition_map[flag]
            else:
                return f"{condition_map[flag]} in {location}"
        
        # Handle custom conditions with simple formatting
        flag_words = flag.replace('_', ' ').title()
        
        if location == "Global":
            return flag_words
        else:
            return f"{flag_words} in {location}"