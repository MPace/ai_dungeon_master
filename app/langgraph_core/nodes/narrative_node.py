# app/langgraph_core/nodes/narrative_node.py
"""
Narrative Update Node for LangGraph

This node handles state changes resulting from validated player actions
and checks for narrative triggers based on the new state.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re

from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.narrative_tools import (
    NarrativeTriggerEvaluatorTool,
    AdvanceTimeTool,
    CalculateTravelTimeTool,
    UpdateQuestStatusTool,
    SetGlobalFlagTool,
    SetAreaFlagTool
)
from app.models.campaign_module import CampaignModule

logger = logging.getLogger(__name__)

class NarrativeNode:
    """Node for updating narrative state in the LangGraph"""
    
    def __init__(self):
        """Initialize narrative node with narrative tools"""
        self.trigger_evaluator = NarrativeTriggerEvaluatorTool()
        self.advance_time_tool = AdvanceTimeTool()
        self.travel_time_calculator = CalculateTravelTimeTool()
        self.quest_updater = UpdateQuestStatusTool()
        self.global_flag_setter = SetGlobalFlagTool()
        self.area_flag_setter = SetAreaFlagTool()
    
    def __call__(self, state: AIGameState) -> AIGameState:
        """
        Update narrative state based on player action and check for triggers
        
        Args:
            state: Current game state after validation
            
        Returns:
            Updated state with narrative changes
        """
        try:
            # Extract player intent and validation result from state
            intent_data = state.get("intent_data", {})
            validation_result = state.get("validation_result", {})
            
            if not validation_result.get("status", False):
                logger.warning("Skipping narrative update due to failed validation")
                return state
            
            # Extract relevant data
            intent = intent_data.get("intent", "")
            slots = intent_data.get("slots", {})
            
            # Handle game state transitions based on player actions
            self._handle_game_state_transitions(state, intent, slots)
            
            # Apply direct state changes based on intent
            self._apply_direct_state_changes(state, intent, slots, validation_result)
            
            # Handle time advancement for actions that involve movement or time
            if intent in ["explore", "rest"] or self._involves_movement(intent, slots):
                self._handle_time_advancement(state, intent, slots)
            
            # Check for narrative triggers based on the new state
            self._evaluate_narrative_triggers(state)
            
            # Apply default time advancement if no specific time-advancing action
            if intent not in ["rest", "explore"] and not self._involves_movement(intent, slots):
                # Add a small time advancement (e.g., 5-10 minutes) for most actions
                self._apply_default_time_advancement(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error in narrative node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return state
    
    def _handle_game_state_transitions(self, state: AIGameState, 
                                     intent: str, slots: Dict[str, Any]) -> None:
        """
        Handle game state transitions based on player actions
        
        Args:
            state: Current game state
            intent: Player's intent
            slots: Intent slots
        """
        current_state = state.get("game_state", "exploration")
        new_state = current_state
        
        # Store previous state for transition detection
        state["previous_game_state"] = current_state
        
        # Handle transitions based on current state and intent
        if current_state != "combat":
            # Check if action initiates combat
            if intent in ["weapon_attack", "cast_spell"]:
                # Check if it's offensive
                if self._is_offensive_action(state, intent, slots):
                    new_state = "combat"
                    logger.info(f"Transitioning to combat state due to offensive action: {intent}")
        
        # Rest transitions
        if intent == "rest":
            # Resting is a temporary state that reverts back to exploration
            new_state = "resting"
            logger.info("Transitioning to resting state")
        
        # Social interaction transitions
        if intent == "action" and current_state != "social":
            action = slots.get("action", "").lower()
            if action in ["persuade", "intimidate", "deceive", "talk", "speak"]:
                # Check if there's an NPC target
                if self._has_npc_target(state):
                    new_state = "social"
                    logger.info(f"Transitioning to social state due to social action: {action}")
        
        # Exploration transitions
        if intent == "explore" and current_state not in ["combat", "resting"]:
            new_state = "exploration"
            logger.info("Transitioning to exploration state")
        
        # Escape/flee transitions
        if intent == "action" and slots.get("action", "").lower() in ["flee", "escape", "run"]:
            if current_state == "combat":
                # Fleeing from combat typically returns to exploration
                new_state = "exploration"
                logger.info("Transitioning from combat to exploration due to flee action")
            elif current_state == "social":
                # Leaving a conversation returns to exploration
                new_state = "exploration"
                logger.info("Transitioning from social to exploration due to exit action")
        
        # Update game state if changed
        if new_state != current_state:
            state["game_state"] = new_state
            logger.info(f"Game state transitioned from {current_state} to {new_state}")
    
    def _is_offensive_action(self, state: AIGameState, intent: str, slots: Dict[str, Any]) -> bool:
        """
        Check if the action is offensive (likely to start combat)
        
        Args:
            state: Current game state
            intent: Player's intent
            slots: Intent slots
            
        Returns:
            bool: True if action is offensive
        """
        if intent == "weapon_attack":
            return True
        
        if intent == "cast_spell":
            spell_name = slots.get("spell_name", "").lower()
            
            # First, try to look up the spell in the campaign module
            campaign_module_id = state.get("campaign_module_id")
            if campaign_module_id:
                try:
                    campaign_module = CampaignModule.load(campaign_module_id)
                    if campaign_module and hasattr(campaign_module, 'spells'):
                        spell_data = None
                        # Search for spell in the module
                        for spell in campaign_module.spells:
                            if isinstance(spell, dict) and spell.get("name", "").lower() == spell_name:
                                spell_data = spell
                                break
                        
                        if spell_data:
                            # Check if the spell has damage or harmful effects
                            if spell_data.get("damage"):
                                return True
                            
                            # Check for harmful effects
                            school = spell_data.get("school", "").lower()
                            if school in ["evocation", "necromancy", "enchantment"]:
                                # Check description for harmful keywords
                                description = spell_data.get("description", "").lower()
                                harmful_keywords = ["damage", "harm", "kill", "destroy", "wound", "control", "curse"]
                                if any(keyword in description for keyword in harmful_keywords):
                                    return True
                except Exception as e:
                    logger.warning(f"Could not load campaign module for spell data: {e}")
            
            # Fallback to keyword-based detection
            offensive_keywords = [
                "bolt", "blast", "missile", "arrow", "fire", "ice", "lightning",
                "thunder", "acid", "poison", "necrotic", "ray", "strike", 
                "smite", "attack", "damage", "wound", "harm"
            ]
            
            return any(keyword in spell_name for keyword in offensive_keywords)
        
        return False
    
    def _has_npc_target(self, state: AIGameState) -> bool:
        """
        Check if there's an NPC target for social interaction
        
        Args:
            state: Current game state
            
        Returns:
            bool: True if NPC target exists
        """
        # Check player input for NPC names/references
        player_input = state.get("player_input", "").lower()
        
        # Check if current location has NPCs
        current_location = state.get("current_location_id")
        if not current_location:
            return False
        
        # Get campaign module to check for NPCs
        campaign_module_id = state.get("campaign_module_id")
        if not campaign_module_id:
            return False
        
        campaign_module = CampaignModule.load(campaign_module_id)
        
        if campaign_module and current_location in campaign_module.locations:
            location = campaign_module.locations[current_location]
            npcs_present = location.get("npcs_present", [])
            
            # Check if any NPC names are mentioned in player input
            for npc_id in npcs_present:
                npc = campaign_module.get_npc(npc_id)
                if npc and "name" in npc:
                    npc_name = npc["name"].lower()
                    # Check for full name or partial matches
                    if npc_name in player_input:
                        return True
                    # Check for first/last name matches
                    name_parts = npc_name.split()
                    if any(part in player_input for part in name_parts):
                        return True
        
        # Check for general social keywords that indicate NPC interaction
        social_keywords = ["talk to", "speak with", "ask", "tell", "say to", "question", "greet", "approach"]
        
        # Check for pronouns that might refer to NPCs
        pronoun_keywords = ["him", "her", "them", "the man", "the woman", "the guard", "the merchant"]
        
        return any(keyword in player_input for keyword in social_keywords) or \
               any(pronoun in player_input for pronoun in pronoun_keywords)
    
    def _apply_direct_state_changes(self, state: AIGameState, 
                                 intent: str, slots: Dict[str, Any],
                                 validation_result: Dict[str, Any]) -> None:
        """
        Apply direct state changes resulting from validated player actions
        
        Args:
            state: Current game state
            intent: Player's intent
            slots: Intent slots
            validation_result: Validation result with details
        """
        # Get narrative state from the state object
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Handle specific intents
        if intent == "manage_item":
            action_type = slots.get("action_type", "")
            item_name = slots.get("item_name", "")
            details = validation_result.get("details", {})
            
            if action_type == "take":
                # Item acquisition would be handled by the mechanics node
                # Here we just set a flag that an item was taken
                if "global_flags" not in narrative_state:
                    narrative_state["global_flags"] = []
                
                item_taken_flag = f"item_taken_{item_name.lower().replace(' ', '_')}"
                if item_taken_flag not in narrative_state["global_flags"]:
                    narrative_state["global_flags"].append(item_taken_flag)
            
            elif action_type == "drop":
                # Mark that item was dropped at current location
                location_id = state.get("current_location_id")
                if location_id:
                    if "location_states" not in narrative_state:
                        narrative_state["location_states"] = {}
                    
                    if location_id not in narrative_state["location_states"]:
                        narrative_state["location_states"][location_id] = {}
                    
                    # Add item to location's dropped items
                    location_state = narrative_state["location_states"][location_id]
                    if "dropped_items" not in location_state:
                        location_state["dropped_items"] = []
                    
                    if item_name not in location_state["dropped_items"]:
                        location_state["dropped_items"].append(item_name)
            
            elif action_type == "equip" or action_type == "unequip":
                # Set equipment change flag
                if "global_flags" not in narrative_state:
                    narrative_state["global_flags"] = []
                
                equip_flag = f"equipment_changed_{item_name.lower().replace(' ', '_')}"
                if equip_flag not in narrative_state["global_flags"]:
                    narrative_state["global_flags"].append(equip_flag)
        
        elif intent == "explore":
            # Record exploration in the narrative state
            sensory_type = slots.get("sensory_type", "visual")
            location_id = state.get("current_location_id")
            
            if location_id:
                # Update location state to mark it as explored
                if "location_states" not in narrative_state:
                    narrative_state["location_states"] = {}
                
                if location_id not in narrative_state["location_states"]:
                    narrative_state["location_states"][location_id] = {}
                
                # Mark exploration type
                exploration_key = f"explored_{sensory_type}"
                narrative_state["location_states"][location_id][exploration_key] = True
                
                # Set timestamp
                exploration_time_key = f"last_explored_{sensory_type}"
                narrative_state["location_states"][location_id][exploration_time_key] = datetime.utcnow().isoformat()
        
        elif intent == "use_feature":
            # Track feature use
            feature_name = slots.get("feature_name", "")
            if "global_flags" not in narrative_state:
                narrative_state["global_flags"] = []
            
            feature_used_flag = f"feature_used_{feature_name.lower().replace(' ', '_')}"
            narrative_state["global_flags"].append(feature_used_flag)
            
            # Track feature uses count
            if "feature_use_counts" not in narrative_state:
                narrative_state["feature_use_counts"] = {}
            
            if feature_name not in narrative_state["feature_use_counts"]:
                narrative_state["feature_use_counts"][feature_name] = 0
            
            narrative_state["feature_use_counts"][feature_name] += 1
        
        elif intent == "use_item":
            # Track item use
            item_name = slots.get("item_name", "")
            if "global_flags" not in narrative_state:
                narrative_state["global_flags"] = []
            
            item_used_flag = f"item_used_{item_name.lower().replace(' ', '_')}"
            narrative_state["global_flags"].append(item_used_flag)
        
        # Handle combat outcomes
        elif intent == "weapon_attack" and state.get("game_state") == "combat":
            # Set flag for combat engagement
            if "global_flags" not in narrative_state:
                narrative_state["global_flags"] = []
            
            combat_flag = "player_initiated_combat"
            if combat_flag not in narrative_state["global_flags"]:
                narrative_state["global_flags"].append(combat_flag)
        
        elif intent == "cast_spell":
            # Track spell casting
            spell_name = slots.get("spell_name", "")
            if "global_flags" not in narrative_state:
                narrative_state["global_flags"] = []
            
            spell_cast_flag = f"spell_cast_{spell_name.lower().replace(' ', '_')}"
            narrative_state["global_flags"].append(spell_cast_flag)
            
            # Track spell use count
            if "spell_cast_counts" not in narrative_state:
                narrative_state["spell_cast_counts"] = {}
            
            if spell_name not in narrative_state["spell_cast_counts"]:
                narrative_state["spell_cast_counts"][spell_name] = 0
            
            narrative_state["spell_cast_counts"][spell_name] += 1
        
        elif intent == "action":
            # Track general actions
            action = slots.get("action", "")
            skill = slots.get("skill", "")
            
            if "global_flags" not in narrative_state:
                narrative_state["global_flags"] = []
            
            action_flag = f"action_performed_{action.lower().replace(' ', '_')}"
            narrative_state["global_flags"].append(action_flag)
            
            if skill:
                skill_flag = f"skill_used_{skill.lower().replace(' ', '_')}"
                narrative_state["global_flags"].append(skill_flag)
        
        # Update the state with modified narrative state
        state["tracked_narrative_state"] = narrative_state
    
    def _involves_movement(self, intent: str, slots: Dict[str, Any]) -> bool:
        """
        Check if the intent involves movement/travel
        
        Args:
            intent: Player's intent
            slots: Intent slots
            
        Returns:
            bool: True if movement is involved
        """
        # Check for movement-related intents or keywords
        if intent == "explore" and "move" in slots.get("action", "").lower():
            return True
        
        # Check for travel keywords in player input
        if intent == "action":
            action = slots.get("action", "").lower()
            movement_actions = ["move", "travel", "walk", "run", "go", "head", "journey", "proceed", "advance"]
            return any(move_action in action for move_action in movement_actions)
        
        return False
    
    def _handle_time_advancement(self, state: AIGameState, intent: str, 
                              slots: Dict[str, Any]) -> None:
        """
        Handle time advancement for actions that involve time passing
        
        Args:
            state: Current game state
            intent: Player's intent
            slots: Intent slots
        """
        # Get current location for travel calculations
        current_location_id = state.get("current_location_id")
        
        # Calculate time advancement based on intent
        if intent == "rest":
            rest_duration = slots.get("duration", "short")
            
            # Calculate rest duration
            if rest_duration == "long":
                # Long rest is 8 hours
                self.advance_time_tool.advance_time(
                    state=state,
                    duration=timedelta(hours=8),
                    action_type="rest"
                )
            else:
                # Short rest is 1 hour
                self.advance_time_tool.advance_time(
                    state=state,
                    duration=timedelta(hours=1),
                    action_type="rest"
                )
            
        elif self._involves_movement(intent, slots):
            # Extract travel details from state
            destination, distance, travel_mode = self._extract_travel_details(state, intent, slots)
            
            # Calculate travel time based on extracted details
            travel_duration = self.travel_time_calculator.calculate_travel_time(
                state=state,
                distance=distance,
                travel_mode=travel_mode
            )
            
            # Advance time
            self.advance_time_tool.advance_time(
                state=state,
                duration=travel_duration,
                action_type="travel",
                distance=distance
            )
            
            # Update current location if a destination was determined
            if destination:
                state["current_location_id"] = destination
            
        elif intent == "explore":
            # Exploration typically takes some time
            # Usually around 10-30 minutes
            explore_duration = timedelta(minutes=20)
            
            # Advance time
            self.advance_time_tool.advance_time(
                state=state,
                duration=explore_duration,
                action_type="explore"
            )
    
    def _extract_travel_details(self, state: AIGameState, intent: str, 
                              slots: Dict[str, Any]) -> Tuple[Optional[str], float, str]:
        """
        Extract travel destination, distance, and mode from state
        
        Args:
            state: Current game state
            intent: Player's intent
            slots: Intent slots
            
        Returns:
            Tuple of (destination, distance, travel_mode)
        """
        # Default values
        destination = None
        distance = 1.0  # Default to 1 mile
        travel_mode = "walk"  # Default to walking
        
        # Try to extract from slots
        if "destination" in slots:
            destination = slots["destination"]
        if "distance" in slots:
            try:
                distance = float(slots["distance"])
            except ValueError:
                pass
        if "travel_mode" in slots:
            travel_mode = slots["travel_mode"]
        
        # If no destination in slots, try to parse from player input
        if not destination:
            player_input = state.get("player_input", "").lower()
            campaign_module_id = state.get("campaign_module_id")
            current_location_id = state.get("current_location_id")
            
            if campaign_module_id and current_location_id:
                campaign_module = CampaignModule.load(campaign_module_id)
                
                if campaign_module and current_location_id in campaign_module.locations:
                    current_location = campaign_module.locations[current_location_id]
                    connections = current_location.get("connections", [])
                    
                    # Check if any connected location is mentioned in player input
                    for connected_location_id in connections:
                        if connected_location_id in campaign_module.locations:
                            connected_location = campaign_module.locations[connected_location_id]
                            location_name = connected_location.get("name", "").lower()
                            
                            if location_name and location_name in player_input:
                                destination = connected_location_id
                                
                                # Try to extract distance from location data
                                if isinstance(connections, dict) and connected_location_id in connections:
                                    connection_data = connections[connected_location_id]
                                    if isinstance(connection_data, dict) and "distance" in connection_data:
                                        distance = connection_data["distance"]
                                
                                break
        
        # Extract travel mode from player input if not in slots
        if travel_mode == "walk":
            player_input = state.get("player_input", "").lower()
            travel_mode_keywords = {
                "run": "run",
                "ride": "horse",
                "horseback": "horse",
                "cart": "wagon",
                "wagon": "wagon",
                "boat": "boat",
                "ship": "ship",
                "sail": "ship",
                "swim": "swim",
                "fly": "flying"
            }
            
            for keyword, mode in travel_mode_keywords.items():
                if keyword in player_input:
                    travel_mode = mode
                    break
        
        return destination, distance, travel_mode
    
    def _evaluate_narrative_triggers(self, state: AIGameState) -> None:
        """
        Check for narrative triggers based on the current state
        
        Args:
            state: Current game state
        """
        # Use the NarrativeTriggerEvaluatorTool to check for triggers
        triggered_events = self.trigger_evaluator.evaluate_triggers(state)
        
        # Process each triggered event
        for event in triggered_events:
            outcomes = event.get("outcomes", [])
            event_id = event.get("id", "unknown_event")
            
            for outcome in outcomes:
                action_type = outcome.get("action_type", "")
                parameters = outcome.get("parameters", {})
                
                # Apply the outcome based on action type
                if action_type == "update_quest":
                    quest_id = parameters.get("quest_id", "")
                    stage_id = parameters.get("stage_id", "")
                    
                    if quest_id and stage_id:
                        self.quest_updater.update_quest_status(
                            state=state,
                            quest_id=quest_id,
                            stage_id=stage_id
                        )
                        
                elif action_type == "set_global_flag":
                    flag_name = parameters.get("flag_name", "")
                    flag_value = parameters.get("value", True)
                    
                    if flag_name:
                        self.global_flag_setter.set_global_flag(
                            state=state,
                            flag_name=flag_name,
                            value=flag_value
                        )
                        
                elif action_type == "set_area_flag":
                    location_id = parameters.get("location_id", "")
                    flag_name = parameters.get("flag_name", "")
                    flag_value = parameters.get("value", True)
                    
                    if location_id and flag_name:
                        self.area_flag_setter.set_area_flag(
                            state=state,
                            location_id_or_region=location_id,
                            flag_name=flag_name,
                            value=flag_value
                        )
                
                elif action_type == "modify_npc_disposition":
                    npc_id = parameters.get("npc_id", "")
                    disposition = parameters.get("disposition", "")
                    
                    if npc_id and disposition:
                        narrative_state = state.get("tracked_narrative_state", {})
                        if "npc_dispositions" not in narrative_state:
                            narrative_state["npc_dispositions"] = {}
                        
                        narrative_state["npc_dispositions"][npc_id] = disposition
                        state["tracked_narrative_state"] = narrative_state
                
                elif action_type == "add_inventory_item":
                    item_id = parameters.get("item_id", "")
                    quantity = parameters.get("quantity", 1)
                    
                    if item_id:
                        # This should be handled by the mechanics node, but we can set a flag
                        narrative_state = state.get("tracked_narrative_state", {})
                        if "global_flags" not in narrative_state:
                            narrative_state["global_flags"] = []
                        
                        item_flag = f"item_granted_{item_id}"
                        narrative_state["global_flags"].append(item_flag)
                        state["tracked_narrative_state"] = narrative_state
                
                elif action_type == "spawn_npc":
                    npc_id = parameters.get("npc_id", "")
                    location_id = parameters.get("location_id", "")
                    
                    if npc_id and location_id:
                        narrative_state = state.get("tracked_narrative_state", {})
                        if "location_states" not in narrative_state:
                            narrative_state["location_states"] = {}
                        
                        if location_id not in narrative_state["location_states"]:
                            narrative_state["location_states"][location_id] = {}
                        
                        location_state = narrative_state["location_states"][location_id]
                        if "npcs_present" not in location_state:
                            location_state["npcs_present"] = []
                        
                        if npc_id not in location_state["npcs_present"]:
                            location_state["npcs_present"].append(npc_id)
                        
                        state["tracked_narrative_state"] = narrative_state
            
            # Record first-time events
            if event.get("first_time", False):
                self.global_flag_setter.set_global_flag(
                    state=state,
                    flag_name=f"event_fired_{event_id}",
                    value=True
                )
    
    def _apply_default_time_advancement(self, state: AIGameState) -> None:
        """
        Apply a small default time advancement for actions that don't
        explicitly involve time passing
        
        Args:
            state: Current game state
        """
        # Default to a short time advancement (5-10 minutes)
        default_duration = timedelta(minutes=5)
        
        # Advance time
        self.advance_time_tool.advance_time(
            state=state,
            duration=default_duration,
            action_type="default"
        )

# Create a singleton instance
narrative_node = NarrativeNode()

# Function to use as node in graph
def process_narrative(state: AIGameState) -> AIGameState:
    """Process narrative update for player actions"""
    return narrative_node(state)