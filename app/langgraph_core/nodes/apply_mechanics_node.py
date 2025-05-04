# app/langgraph_core/nodes/apply_mechanics_node.py
"""
Apply Mechanics Node for LangGraph

This node parses mechanical effects from the AI DM's response and applies them
to the game state, including character stats, resources, conditions, timing,
and game state transitions based on the DM's narrative.
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import timedelta

from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.narrative_tools import AdvanceTimeTool
from app.extensions import get_db

logger = logging.getLogger(__name__)

class ApplyMechanicsNode:
    """Node for applying mechanical effects from AI DM responses"""
    
    def __init__(self):
        """Initialize mechanics node with necessary tools"""
        self.advance_time_tool = AdvanceTimeTool()
        # Note: ExecuteRestMechanicsTool would be imported here when implemented
        # from app.langgraph_core.tools.mechanics_tools import ExecuteRestMechanicsTool
        # self.rest_mechanics_tool = ExecuteRestMechanicsTool()
    
    def __call__(self, state: AIGameState) -> AIGameState:
        """
        Parse and apply mechanical effects from the AI DM response
        
        Args:
            state: Current game state with DM response
            
        Returns:
            Updated state with applied mechanics
        """
        try:
            # Get the DM response
            dm_response = state.get("dm_response", "")
            if not dm_response:
                logger.warning("No DM response to parse for mechanics")
                return state
            
            # Get character data
            character_id = state.get("current_character_id")
            if not character_id:
                logger.warning("No character ID in state for mechanics application")
                return state
            
            # First check for game state transitions in the DM response
            self._check_and_apply_state_transitions(state, dm_response)
            
            # Check if we have structured mechanics data from the AI DM node
            if "parsed_mechanics" in state:
                mechanics_to_apply = state["parsed_mechanics"]
                logger.info("Using structured mechanics data from AI DM node")
            else:
                # Fall back to parsing the response for mechanical effects
                mechanics_to_apply = self._parse_mechanical_effects(dm_response)
                logger.info("Using regex parsing for mechanics extraction")
            
            # Apply each mechanical effect
            for mechanic in mechanics_to_apply:
                mechanic_type = mechanic.get("type")
                data = mechanic.get("data", {})
                
                # Determine the target of the effect
                target_id = self._determine_target(state, mechanic, dm_response)
                
                if mechanic_type == "damage":
                    self._apply_damage(state, target_id, data)
                elif mechanic_type == "healing":
                    self._apply_healing(state, target_id, data)
                elif mechanic_type == "condition":
                    self._apply_condition(state, target_id, data)
                elif mechanic_type == "resource_change":
                    self._apply_resource_change(state, target_id, data)
                elif mechanic_type == "rest_complete":
                    self._apply_rest_mechanics(state, target_id, data)
                elif mechanic_type == "ability_check":
                    self._record_ability_check(state, target_id, data)
                elif mechanic_type == "combat_roll":
                    self._record_combat_roll(state, target_id, data)
                else:
                    logger.warning(f"Unknown mechanic type: {mechanic_type}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in apply mechanics node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return state
    
    def _determine_target(self, state: AIGameState, mechanic: Dict[str, Any], 
                         dm_response: str) -> str:
        """
        Determine the target of a mechanical effect
        
        Args:
            state: Current game state
            mechanic: The mechanical effect to apply
            dm_response: The DM's response text
            
        Returns:
            str: Target ID (character_id for player, npc_id for NPCs)
        """
        # Check if target is explicitly specified in the mechanic data
        if "target" in mechanic.get("data", {}):
            return mechanic["data"]["target"]
        
        # Check for target in the mechanic data
        target_info = mechanic.get("data", {}).get("target_info", {})
        if target_info:
            if target_info.get("type") == "player":
                return state.get("current_character_id", "")
            elif target_info.get("type") == "npc":
                return target_info.get("id", "")
        
        # Default to player character if no specific target
        return state.get("current_character_id", "")
    
    def _apply_damage(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Apply damage to character"""
        amount = data.get("amount", 0)
        if amount <= 0:
            return
        
        # Get narrative state
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Initialize character_stats if not present
        if "character_stats" not in narrative_state:
            narrative_state["character_stats"] = {}
        
        # Initialize target's stats if not present
        if target_id not in narrative_state["character_stats"]:
            narrative_state["character_stats"][target_id] = self._initialize_character_stats(state, target_id)
        
        character_stats = narrative_state["character_stats"][target_id]
        
        # Apply damage to hit points
        current_hp = character_stats.get("hit_points", {}).get("current", 0)
        new_hp = max(0, current_hp - amount)  # HP can't go below 0
        
        # Update the character's hit points in state
        character_stats["hit_points"]["current"] = new_hp
        
        # Check for unconsciousness
        if new_hp == 0 and current_hp > 0:
            conditions = character_stats.get("conditions", [])
            if "unconscious" not in conditions:
                conditions.append("unconscious")
                character_stats["conditions"] = conditions
        
        # Update the narrative state
        state["tracked_narrative_state"] = narrative_state
        
        logger.info(f"Applied {amount} damage to {target_id}. HP: {current_hp} -> {new_hp}")
    
    def _apply_healing(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Apply healing to character"""
        amount = data.get("amount", 0)
        if amount <= 0:
            return
        
        # Get narrative state
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Initialize character_stats if not present
        if "character_stats" not in narrative_state:
            narrative_state["character_stats"] = {}
        
        # Initialize target's stats if not present
        if target_id not in narrative_state["character_stats"]:
            narrative_state["character_stats"][target_id] = self._initialize_character_stats(state, target_id)
        
        character_stats = narrative_state["character_stats"][target_id]
        
        # Apply healing to hit points
        current_hp = character_stats.get("hit_points", {}).get("current", 0)
        max_hp = character_stats.get("hit_points", {}).get("max", 1)
        new_hp = min(max_hp, current_hp + amount)  # HP can't exceed max
        
        # Update the character's hit points in state
        character_stats["hit_points"]["current"] = new_hp
        
        # Remove unconscious condition if healed above 0
        if new_hp > 0 and current_hp == 0:
            conditions = character_stats.get("conditions", [])
            if "unconscious" in conditions:
                conditions.remove("unconscious")
                character_stats["conditions"] = conditions
        
        # Update the narrative state
        state["tracked_narrative_state"] = narrative_state
        
        logger.info(f"Applied {amount} healing to {target_id}. HP: {current_hp} -> {new_hp}")
    
    def _apply_condition(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Apply or remove a condition to/from character"""
        condition = data.get("condition", "")
        action = data.get("action", "add")
        
        if not condition:
            return
        
        # Get narrative state
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Initialize character_stats if not present
        if "character_stats" not in narrative_state:
            narrative_state["character_stats"] = {}
        
        # Initialize target's stats if not present
        if target_id not in narrative_state["character_stats"]:
            narrative_state["character_stats"][target_id] = self._initialize_character_stats(state, target_id)
        
        character_stats = narrative_state["character_stats"][target_id]
        
        # Get current conditions
        conditions = character_stats.get("conditions", [])
        
        if action == "add":
            if condition not in conditions:
                conditions.append(condition)
                character_stats["conditions"] = conditions
                logger.info(f"Added condition {condition} to {target_id}")
        
        elif action == "remove":
            if condition in conditions:
                conditions.remove(condition)
                character_stats["conditions"] = conditions
                logger.info(f"Removed condition {condition} from {target_id}")
        
        # Update the narrative state
        state["tracked_narrative_state"] = narrative_state
    
    def _apply_resource_change(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Apply resource changes to character (spell slots, abilities, etc.)"""
        resource_type = data.get("resource_type", "")
        resource_key = data.get("resource_key", "")
        change_amount = data.get("change_amount", 0)
        
        if not resource_type or not resource_key:
            return
        
        # Get narrative state
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Initialize character_stats if not present
        if "character_stats" not in narrative_state:
            narrative_state["character_stats"] = {}
        
        # Initialize target's stats if not present
        if target_id not in narrative_state["character_stats"]:
            narrative_state["character_stats"][target_id] = self._initialize_character_stats(state, target_id)
        
        character_stats = narrative_state["character_stats"][target_id]
        
        # Apply resource change based on type
        if resource_type == "spell_slot":
            if "spell_slots" not in character_stats:
                character_stats["spell_slots"] = {}
            
            spell_slots = character_stats["spell_slots"]
            if resource_key not in spell_slots:
                spell_slots[resource_key] = {"current": 0, "max": 0}
            
            current = spell_slots[resource_key].get("current", 0)
            max_slots = spell_slots[resource_key].get("max", 0)
            new_value = max(0, min(max_slots, current + change_amount))
            
            spell_slots[resource_key]["current"] = new_value
            logger.info(f"Updated spell slot {resource_key} for {target_id}: {current} -> {new_value}")
        
        elif resource_type == "class_resource":
            if "class_resources" not in character_stats:
                character_stats["class_resources"] = {}
            
            class_resources = character_stats["class_resources"]
            if resource_key not in class_resources:
                class_resources[resource_key] = {"current": 0, "max": 0}
            
            current = class_resources[resource_key].get("current", 0)
            max_resource = class_resources[resource_key].get("max", 0)
            new_value = max(0, min(max_resource, current + change_amount))
            
            class_resources[resource_key]["current"] = new_value
            logger.info(f"Updated class resource {resource_key} for {target_id}: {current} -> {new_value}")
        
        elif resource_type == "item_charge":
            if "item_charges" not in character_stats:
                character_stats["item_charges"] = {}
            
            item_charges = character_stats["item_charges"]
            if resource_key not in item_charges:
                item_charges[resource_key] = {"current": 0, "max": 0}
            
            current = item_charges[resource_key].get("current", 0)
            max_charges = item_charges[resource_key].get("max", 0)
            new_value = max(0, min(max_charges, current + change_amount))
            
            item_charges[resource_key]["current"] = new_value
            logger.info(f"Updated item charges {resource_key} for {target_id}: {current} -> {new_value}")
        
        # Update the narrative state
        state["tracked_narrative_state"] = narrative_state
    
    def _apply_rest_mechanics(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Apply rest mechanics to character"""
        rest_type = data.get("rest_type", "short")
        
        # Get narrative state
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Initialize character_stats if not present
        if "character_stats" not in narrative_state:
            narrative_state["character_stats"] = {}
        
        # Initialize target's stats if not present
        if target_id not in narrative_state["character_stats"]:
            narrative_state["character_stats"][target_id] = self._initialize_character_stats(state, target_id)
        
        character_stats = narrative_state["character_stats"][target_id]
        
        # TODO: When ExecuteRestMechanicsTool is implemented, use it here
        # For now, implement basic rest mechanics
        
        if rest_type == "long":
            # Long rest mechanics
            hit_points = character_stats.get("hit_points", {})
            max_hp = hit_points.get("max", 1)
            hit_points["current"] = max_hp
            
            # Restore all spell slots
            if "spell_slots" in character_stats:
                for level, slots in character_stats["spell_slots"].items():
                    if isinstance(slots, dict):
                        slots["current"] = slots.get("max", 0)
            
            # Restore class resources
            if "class_resources" in character_stats:
                for resource, data in character_stats["class_resources"].items():
                    if isinstance(data, dict):
                        data["current"] = data.get("max", 0)
            
            # Remove most conditions
            conditions_to_keep = ["exhaustion"]  # Some conditions persist
            current_conditions = character_stats.get("conditions", [])
            new_conditions = [c for c in current_conditions if c in conditions_to_keep]
            character_stats["conditions"] = new_conditions
            
            # Restore hit dice (half of total)
            if "hit_dice" in character_stats:
                total_hit_dice = character_stats["hit_dice"].get("max", 1)
                current_hit_dice = character_stats["hit_dice"].get("current", 0)
                restored_hit_dice = max(1, total_hit_dice // 2)
                character_stats["hit_dice"]["current"] = min(total_hit_dice, current_hit_dice + restored_hit_dice)
            
            logger.info(f"Applied long rest mechanics to {target_id}")
            
            # Advance time by 8 hours
            self.advance_time_tool.advance_time(
                state=state,
                duration=timedelta(hours=8),
                action_type="long_rest"
            )
        
        else:  # short rest
            # Short rest mechanics
            # Players can spend hit dice to heal
            if "hit_dice" in character_stats:
                available_hit_dice = character_stats["hit_dice"].get("current", 0)
                if available_hit_dice > 0:
                    # This is simplified - in reality, players choose how many to spend
                    hit_dice_to_spend = min(available_hit_dice, 2)  # Spend up to 2
                    character_stats["hit_dice"]["current"] -= hit_dice_to_spend
                    
                    # Heal based on hit dice (simplified)
                    healing = hit_dice_to_spend * 6  # Assume d8 hit dice average
                    current_hp = character_stats["hit_points"]["current"]
                    max_hp = character_stats["hit_points"]["max"]
                    new_hp = min(max_hp, current_hp + healing)
                    character_stats["hit_points"]["current"] = new_hp
            
            # Some class resources recover on short rest
            if "class_resources" in character_stats:
                for resource, data in character_stats["class_resources"].items():
                    if isinstance(data, dict) and data.get("short_rest_recovery", False):
                        data["current"] = data.get("max", 0)
            
            logger.info(f"Applied short rest mechanics to {target_id}")
            
            # Advance time by 1 hour
            self.advance_time_tool.advance_time(
                state=state,
                duration=timedelta(hours=1),
                action_type="short_rest"
            )
        
        # Update the narrative state
        state["tracked_narrative_state"] = narrative_state
    
    def _initialize_character_stats(self, state: AIGameState, character_id: str) -> Dict[str, Any]:
        """
        Initialize character stats from the database
        
        Args:
            state: Current game state
            character_id: ID of the character
            
        Returns:
            Dict containing initialized character stats
        """
        # Try to get character data from database for initialization
        character_data = self._get_character_data(character_id)
        
        if character_data:
            # Initialize from database data
            stats = {
                "hit_points": {
                    "current": character_data.get("hit_points", {}).get("current", 10),
                    "max": character_data.get("hit_points", {}).get("max", 10)
                },
                "conditions": character_data.get("conditions", []),
                "spell_slots": {},
                "class_resources": {},
                "item_charges": {},
                "hit_dice": {
                    "current": character_data.get("level", 1),
                    "max": character_data.get("level", 1)
                }
            }
            
            # Initialize spell slots if character has spellcasting
            spellcasting = character_data.get("spellcasting", {})
            if "slots" in spellcasting:
                for level, slot_data in spellcasting["slots"].items():
                    if isinstance(slot_data, dict):
                        stats["spell_slots"][level] = {
                            "current": slot_data.get("available", 0),
                            "max": slot_data.get("max", 0)
                        }
                    else:
                        stats["spell_slots"][level] = {
                            "current": slot_data,
                            "max": slot_data
                        }
            
            # Initialize class resources
            features = character_data.get("features", {})
            for feature_category, feature_list in features.items():
                if isinstance(feature_list, list):
                    for feature in feature_list:
                        if isinstance(feature, dict) and "uses" in feature:
                            resource_name = feature.get("name", "Unknown")
                            uses = feature["uses"]
                            if isinstance(uses, dict):
                                stats["class_resources"][resource_name] = {
                                    "current": uses.get("current", 0),
                                    "max": uses.get("max", 0),
                                    "short_rest_recovery": "short rest" in uses.get("recharge", "").lower()
                                }
            
            return stats
        else:
            # Return default stats if character data not found
            return {
                "hit_points": {"current": 10, "max": 10},
                "conditions": [],
                "spell_slots": {},
                "class_resources": {},
                "item_charges": {},
                "hit_dice": {"current": 1, "max": 1}
            }
    
    def _get_character_data(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get character data from database"""
        try:
            db = get_db()
            if db is None:
                return None
            
            character_doc = db.characters.find_one({"character_id": character_id})
            if not character_doc:
                return None
            
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
        except Exception as e:
            logger.error(f"Error getting character data: {e}")
            return None
    
    def _check_and_apply_state_transitions(self, state: AIGameState, dm_response: str) -> None:
        """Check the DM response for state transition indicators"""
        current_state = state.get("game_state", "exploration")
        new_state = current_state
        
        # Store previous state for transition detection
        state["previous_game_state"] = current_state
        
        # Combat start patterns
        combat_start_patterns = [
            r'roll\s+(?:for\s+)?initiative',
            r'combat\s+begins',
            r'attacks?\s+you',
            r'battle\s+(?:begins|starts)',
        ]
        
        # Combat end patterns
        combat_end_patterns = [
            r'(?:enemy|foe|creature)\s+(?:falls|dies|is\s+defeated)',
            r'combat\s+(?:ends|is\s+over)',
            r'victory\s+is\s+yours',
        ]
        
        # Social interaction patterns
        social_start_patterns = [
            r'(?:npc|character)\s+(?:says|speaks|asks)',
            r'conversation\s+begins',
        ]
        
        social_end_patterns = [
            r'conversation\s+ends',
            r'walks?\s+away',
        ]
        
        # Check patterns against response
        if current_state != "combat":
            for pattern in combat_start_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "combat"
                    break
        
        if current_state == "combat":
            for pattern in combat_end_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "exploration"
                    break
        
        # Update game state if changed
        if new_state != current_state:
            state["game_state"] = new_state
            logger.info(f"Game state transitioned from {current_state} to {new_state}")
    
    def _parse_mechanical_effects(self, response: str) -> List[Dict[str, Any]]:
        """Parse mechanical effects from the DM response"""
        mechanics = []
        
        # Parse damage
        damage_patterns = [
            r'takes?\s+(\d+)\s+(?:points?\s+of\s+)?damage',
            r'suffers?\s+(\d+)\s+(?:points?\s+of\s+)?damage',
        ]
        
        for pattern in damage_patterns:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                damage_amount = int(match.group(1))
                mechanics.append({
                    "type": "damage",
                    "data": {"amount": damage_amount}
                })
        
        # Parse healing
        healing_patterns = [
            r'heals?\s+(\d+)\s+(?:hit\s+)?points?',
            r'regains?\s+(\d+)\s+(?:hit\s+)?points?',
        ]
        
        for pattern in healing_patterns:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                healing_amount = int(match.group(1))
                mechanics.append({
                    "type": "healing",
                    "data": {"amount": healing_amount}
                })
        
        # Parse rest completion
        rest_patterns = [
            r'(?:you\s+)?(?:complete|finish)(?:ed)?\s+(?:your\s+)?(?:the\s+)?(long|short)\s+rest',
            r'(?:your\s+)?(?:the\s+)?(long|short)\s+rest\s+(?:is\s+)?(?:completed|finished|over)',
        ]
        
        for pattern in rest_patterns:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                rest_type = match.group(1).lower()
                mechanics.append({
                    "type": "rest_complete",
                    "data": {"rest_type": rest_type}
                })
        
        return mechanics
    
    def _record_ability_check(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Record an ability check request"""
        check_type = data.get("check_type", "")
        if check_type:
            narrative_state = state.get("tracked_narrative_state", {})
            if "pending_checks" not in narrative_state:
                narrative_state["pending_checks"] = []
            
            narrative_state["pending_checks"].append({
                "target_id": target_id,
                "check_type": check_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            state["tracked_narrative_state"] = narrative_state
            logger.info(f"Recorded ability check request: {check_type} for {target_id}")
    
    def _record_combat_roll(self, state: AIGameState, target_id: str, data: Dict[str, Any]) -> None:
        """Record a combat roll request"""
        roll_type = data.get("roll_type", "")
        if roll_type:
            narrative_state = state.get("tracked_narrative_state", {})
            if "pending_rolls" not in narrative_state:
                narrative_state["pending_rolls"] = []
            
            narrative_state["pending_rolls"].append({
                "target_id": target_id,
                "roll_type": roll_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            state["tracked_narrative_state"] = narrative_state
            logger.info(f"Recorded combat roll request: {roll_type} for {target_id}")

# Create a singleton instance
apply_mechanics_node = ApplyMechanicsNode()

# Function to use as node in graph
def process_apply_mechanics(state: AIGameState) -> AIGameState:
    """Apply mechanical effects from AI DM response"""
    return apply_mechanics_node(state)