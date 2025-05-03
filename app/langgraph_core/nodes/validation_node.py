# app/langgraph_core/nodes/validation_node.py
"""
Validation Node for LangGraph

This node validates player intents to ensure they're permissible according
to game rules, character capabilities, and current game state.
"""
import logging
from typing import Dict, Any, List, Optional, Callable

from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.validation_tools import (
    CombatValidatorTool,
    ActionValidatorTool,
    ItemValidatorTool,
    RestFeasibilityCheckTool
)

logger = logging.getLogger(__name__)

class ValidationNode:
    """Node for validating player intents in the LangGraph"""
    
    def __init__(self):
        """Initialize validation node with validation tools"""
        self.combat_validator = CombatValidatorTool()
        self.action_validator = ActionValidatorTool()
        self.item_validator = ItemValidatorTool()
        self.rest_validator = RestFeasibilityCheckTool()
        
        # Map of intent types to validation functions
        self.validation_map = {
            "cast_spell": self._validate_spell_cast,
            "weapon_attack": self._validate_weapon_attack,
            "use_feature": self._validate_feature_use,
            "use_item": self._validate_item_use,
            "action": self._validate_action,
            "explore": self._validate_exploration,
            "manage_item": self._validate_item_management,
            "rest": self._validate_rest,
            # General, recall, and ask_rule don't need validation
            "general": self._always_valid,
            "recall": self._always_valid,
            "ask_rule": self._always_valid
        }
    
    def __call__(self, state: AIGameState) -> AIGameState:
        """
        Validate the player's intent based on game rules and character capabilities
        
        Args:
            state: Current game state with intent data
            
        Returns:
            Updated state with validation result
        """
        try:
            # Extract intent data from state
            intent_data = state.get("intent_data", {})
            intent = intent_data.get("intent", "general")
            slots = intent_data.get("slots", {})
            
            # Get character data from state
            character_id = state.get("current_character_id")
            
            if not character_id:
                logger.warning("No character ID in state, cannot validate")
                state["validation_result"] = {
                    "status": False,
                    "reason": "No character data available for validation",
                    "details": None
                }
                return state
            
            # Get the appropriate validation function for this intent
            validation_func = self.validation_map.get(intent, self._always_valid)
            
            # Perform validation
            logger.info(f"Validating intent: {intent}")
            validation_result = validation_func(state, slots)
            
            # Update state with validation result
            state["validation_result"] = validation_result
            
            # Log validation result
            if validation_result["status"]:
                logger.info(f"Validation passed for intent: {intent}")
            else:
                logger.warning(f"Validation failed for intent: {intent}. Reason: {validation_result['reason']}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in validation node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Set failed validation on error
            state["validation_result"] = {
                "status": False,
                "reason": f"Error during validation: {str(e)}",
                "details": None
            }
            return state
    
    def _validate_spell_cast(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spell casting intent"""
        spell_name = slots.get("spell_name", "")
        is_ritual = slots.get("is_ritual", False)
        
        if not spell_name:
            return {
                "status": False,
                "reason": "No spell name provided",
                "details": None
            }
        
        # Get the current game state
        game_state = state.get("game_state", "exploration")
        character_id = state.get("current_character_id")
        
        # Use the combat validator to check if the spell can be cast
        validation_result = self.combat_validator.validate_spell_cast(
            character_id=character_id,
            spell_name=spell_name,
            is_ritual=is_ritual,
            game_state=game_state
        )
        
        return validation_result
    
    def _validate_weapon_attack(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate weapon attack intent"""
        weapon_name = slots.get("weapon_name", "")
        
        # Get the current game state
        game_state = state.get("game_state", "exploration")
        character_id = state.get("current_character_id")
        
        # Use the combat validator to check if the weapon attack is valid
        validation_result = self.combat_validator.validate_weapon_attack(
            character_id=character_id,
            weapon_name=weapon_name,
            game_state=game_state
        )
        
        return validation_result
    
    def _validate_feature_use(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feature use intent"""
        feature_name = slots.get("feature_name", "")
        resource = slots.get("resource", "")
        
        if not feature_name:
            return {
                "status": False,
                "reason": "No feature name provided",
                "details": None
            }
        
        # Get character data
        character_id = state.get("current_character_id")
        
        # Use the combat validator to check if the feature can be used
        validation_result = self.combat_validator.validate_feature_use(
            character_id=character_id,
            feature_name=feature_name,
            resource=resource
        )
        
        return validation_result
    
    def _validate_item_use(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate item use intent"""
        item_name = slots.get("item_name", "")
        
        if not item_name:
            return {
                "status": False,
                "reason": "No item name provided",
                "details": None
            }
        
        # Get character data
        character_id = state.get("current_character_id")
        
        # Use the item validator to check if the item can be used
        validation_result = self.item_validator.validate_item_use(
            character_id=character_id,
            item_name=item_name
        )
        
        return validation_result
    
    def _validate_action(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action intent"""
        action = slots.get("action", "")
        skill = slots.get("skill", "")
        
        if not action:
            return {
                "status": False,
                "reason": "No action specified",
                "details": None
            }
        
        # Get character data
        character_id = state.get("current_character_id")
        
        # Use the action validator to check if the action is valid
        validation_result = self.action_validator.validate_action(
            character_id=character_id,
            action=action,
            skill=skill
        )
        
        return validation_result
    
    def _validate_exploration(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate exploration intent"""
        sensory_type = slots.get("sensory_type", "visual")
        
        # Exploration is generally always valid
        return {
            "status": True,
            "reason": None,
            "details": {
                "sensory_type": sensory_type
            }
        }
    
    def _validate_item_management(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate item management intent"""
        item_name = slots.get("item_name", "")
        action_type = slots.get("action_type", "")
        
        # Check if this is just an inventory check
        if action_type == "inventory":
            return {
                "status": True,
                "reason": None,
                "details": {
                    "action_type": "inventory"
                }
            }
        
        if not item_name and action_type not in ["inventory"]:
            return {
                "status": False,
                "reason": "No item name provided",
                "details": None
            }
        
        # Get character data
        character_id = state.get("current_character_id")
        
        # Use the item validator to check if the item management action is valid
        validation_result = self.item_validator.validate_item_management(
            character_id=character_id,
            item_name=item_name,
            action_type=action_type
        )
        
        return validation_result
    
    def _validate_rest(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Validate rest intent"""
        duration = slots.get("duration", "short")
        
        # Get the current game state and location
        game_state = state.get("game_state", "exploration")
        location_id = state.get("current_location_id")
        character_id = state.get("current_character_id")
        
        # Use the rest validator to check if resting is possible
        validation_result = self.rest_validator.validate_rest(
            character_id=character_id,
            location_id=location_id,
            duration=duration,
            game_state=game_state,
            narrative_state=state.get("tracked_narrative_state", {})
        )
        
        return validation_result
    
    def _always_valid(self, state: AIGameState, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Default validation function for intents that are always valid"""
        return {
            "status": True,
            "reason": None,
            "details": None
        }

# Create a singleton instance
validation_node = ValidationNode()

# Function to use as node in graph
def process_validation(state: AIGameState) -> AIGameState:
    """Process validation of player intent"""
    return validation_node(state)