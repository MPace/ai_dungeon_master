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
        self.db = get_db()
    
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
            
            # Parse the response for mechanical effects
            mechanics_to_apply = self._parse_mechanical_effects(dm_response)
            
            # Apply each mechanical effect
            for mechanic in mechanics_to_apply:
                mechanic_type = mechanic.get("type")
                data = mechanic.get("data", {})
                
                if mechanic_type == "damage":
                    self._apply_damage(state, character_id, data)
                elif mechanic_type == "healing":
                    self._apply_healing(state, character_id, data)
                elif mechanic_type == "condition":
                    self._apply_condition(state, character_id, data)
                elif mechanic_type == "resource_change":
                    self._apply_resource_change(state, character_id, data)
                elif mechanic_type == "rest_complete":
                    self._apply_rest_mechanics(state, character_id, data)
                elif mechanic_type == "ability_check":
                    self._record_ability_check(state, character_id, data)
                elif mechanic_type == "combat_roll":
                    self._record_combat_roll(state, character_id, data)
                else:
                    logger.warning(f"Unknown mechanic type: {mechanic_type}")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in apply mechanics node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return state
    
    def _check_and_apply_state_transitions(self, state: AIGameState, dm_response: str) -> None:
        """
        Check the DM response for state transition indicators and update the game state
        
        Args:
            state: Current game state
            dm_response: The DM's response text
        """
        current_state = state.get("game_state", "exploration")
        new_state = current_state
        
        # Store previous state for transition detection
        state["previous_game_state"] = current_state
        
        # Check for combat starting
        combat_start_patterns = [
            r'roll\s+(?:for\s+)?initiative',
            r'combat\s+begins',
            r'roll\s+initiative',
            r'attacks?\s+you',
            r'suddenly\s+attacks',
            r'ambush(?:es)?',
            r'hostile\s+(?:creatures?|enemies)',
            r'(?:the\s+)?battle\s+(?:begins|starts|commences)',
            r'charges?\s+(?:at\s+you|forward)',
            r'draws?\s+(?:their\s+)?weapon'
        ]
        
        if current_state != "combat":
            for pattern in combat_start_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "combat"
                    logger.info("DM response indicates combat starting")
                    break
        
        # Check for combat ending
        combat_end_patterns = [
            r'(?:the\s+)?(?:last\s+)?(?:enemy|foe|creature)\s+(?:falls|dies|is\s+defeated)',
            r'combat\s+(?:ends|is\s+over)',
            r'battle\s+(?:ends|is\s+over|concludes)',
            r'you\s+(?:have\s+)?(?:defeated|vanquished)\s+(?:all\s+)?(?:your\s+)?(?:enemies|foes)',
            r'victory\s+is\s+yours',
            r'the\s+fighting\s+(?:ends|stops|ceases)',
            r'all\s+(?:enemies|foes|opponents)\s+(?:are\s+)?(?:defeated|dead|slain)',
            r'peace\s+returns',
            r'danger\s+(?:has\s+)?passed'
        ]
        
        if current_state == "combat":
            for pattern in combat_end_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "exploration"
                    logger.info("DM response indicates combat ending")
                    break
        
        # Check for social interaction starting
        social_start_patterns = [
            r'(?:npc|character)\s+(?:says|speaks|asks|greets)',
            r'(?:"[^"]+"|\'[^\']+\')\s+(?:says|asks|replies)',
            r'you\s+(?:see|notice|encounter)\s+(?:a\s+)?(?:person|figure|humanoid)',
            r'approaches\s+you',
            r'you\s+are\s+(?:approached|greeted)\s+by',
            r'conversation\s+(?:begins|starts)',
            r'starts?\s+(?:talking|speaking|conversing)',
            r'(?:he|she|they)\s+(?:introduces|greets)'
        ]
        
        if current_state == "exploration":
            for pattern in social_start_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "social"
                    logger.info("DM response indicates social interaction starting")
                    break
        
        # Check for social interaction ending
        social_end_patterns = [
            r'(?:the\s+)?(?:conversation|discussion)\s+(?:ends|concludes)',
            r'(?:npc|character)\s+(?:leaves|departs|walks\s+away)',
            r'says?\s+(?:goodbye|farewell)',
            r'turns?\s+(?:away|to\s+leave)',
            r'walks?\s+away',
            r'the\s+(?:person|figure)\s+(?:leaves|disappears)',
            r'end\s+(?:of\s+)?(?:the\s+)?conversation',
            r'you\s+part\s+ways'
        ]
        
        if current_state == "social":
            for pattern in social_end_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "exploration"
                    logger.info("DM response indicates social interaction ending")
                    break
        
        # Check for rest completion
        rest_completion_patterns = [
            r'(?:you\s+)?(?:finish|complete)\s+(?:your\s+)?(?:long|short)\s+rest',
            r'(?:your\s+)?rest\s+(?:is\s+)?(?:completed|finished|over)',
            r'(?:you\s+)?(?:wake|awaken)\s+(?:up\s+)?(?:from\s+your\s+rest|refreshed)',
            r'(?:you\s+)?(?:feel\s+)?(?:rested|refreshed|restored)',
            r'(?:the\s+)?rest\s+(?:period\s+)?(?:ends|is\s+over)'
        ]
        
        if current_state == "resting":
            for pattern in rest_completion_patterns:
                if re.search(pattern, dm_response, re.IGNORECASE):
                    new_state = "exploration"
                    logger.info("DM response indicates rest completion")
                    break
        
        # Update game state if changed
        if new_state != current_state:
            state["game_state"] = new_state
            logger.info(f"Game state transitioned from {current_state} to {new_state} based on DM response")
    
    def _parse_mechanical_effects(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse mechanical effects from the DM response
        
        Args:
            response: The DM's response text
            
        Returns:
            List of mechanical effects to apply
        """
        mechanics = []
        
        # Parse damage (e.g., "takes 10 damage", "suffers 15 points of damage")
        damage_patterns = [
            r'takes?\s+(\d+)\s+(?:points?\s+of\s+)?damage',
            r'suffers?\s+(\d+)\s+(?:points?\s+of\s+)?damage',
            r'loses?\s+(\d+)\s+(?:hit\s+)?points?',
            r'deals?\s+(\d+)\s+(?:points?\s+of\s+)?damage\s+to\s+you',
            r'you\s+take\s+(\d+)\s+(?:points?\s+of\s+)?damage'
        ]
        
        for pattern in damage_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                damage_amount = int(match.group(1))
                mechanics.append({
                    "type": "damage",
                    "data": {"amount": damage_amount}
                })
        
        # Parse healing (e.g., "heals 8 points", "restores 12 hit points")
        healing_patterns = [
            r'heals?\s+(\d+)\s+(?:hit\s+)?points?',
            r'restores?\s+(\d+)\s+(?:hit\s+)?points?',
            r'regains?\s+(\d+)\s+(?:hit\s+)?points?',
            r'you\s+(?:heal|recover)\s+(\d+)\s+(?:hit\s+)?points?'
        ]
        
        for pattern in healing_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                healing_amount = int(match.group(1))
                mechanics.append({
                    "type": "healing",
                    "data": {"amount": healing_amount}
                })
        
        # Parse conditions (e.g., "becomes frightened", "is now poisoned")
        condition_patterns = [
            r'(?:becomes?|is\s+now)\s+(frightened|poisoned|paralyzed|stunned|unconscious|restrained|blinded|charmed|exhausted)',
            r'(?:you\s+)?(?:are|become)\s+(frightened|poisoned|paralyzed|stunned|unconscious|restrained|blinded|charmed|exhausted)',
            r'(?:gains?|suffers?)\s+(?:the\s+)?(frightened|poisoned|paralyzed|stunned|unconscious|restrained|blinded|charmed|exhausted)\s+condition'
        ]
        
        for pattern in condition_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                condition = match.group(1).lower()
                mechanics.append({
                    "type": "condition",
                    "data": {"condition": condition, "action": "add"}
                })
        
        # Parse condition removal (e.g., "is no longer frightened", "removes the poisoned condition")
        condition_removal_patterns = [
            r'(?:is\s+)?no\s+longer\s+(frightened|poisoned|paralyzed|stunned|unconscious|restrained|blinded|charmed|exhausted)',
            r'(?:removes?|ends?)\s+(?:the\s+)?(frightened|poisoned|paralyzed|stunned|unconscious|restrained|blinded|charmed|exhausted)\s+condition',
            r'(?:the\s+)?(frightened|poisoned|paralyzed|stunned|unconscious|restrained|blinded|charmed|exhausted)\s+(?:condition\s+)?(?:ends|is\s+removed)'
        ]
        
        for pattern in condition_removal_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                condition = match.group(1).lower()
                mechanics.append({
                    "type": "condition",
                    "data": {"condition": condition, "action": "remove"}
                })
        
        # Parse ability checks (e.g., "Roll a d20 for Perception", "Make a Strength check")
        ability_check_patterns = [
            r'(?:roll|make)\s+(?:a\s+)?(?:d20\s+)?(?:for\s+)?(?:a\s+)?(strength|dexterity|constitution|intelligence|wisdom|charisma)\s*(?:check)?',
            r'(?:roll|make)\s+(?:a\s+)?(?:d20\s+)?(?:for\s+)?(?:a\s+)?(perception|investigation|athletics|acrobatics|stealth|insight|arcana|nature|religion|medicine|survival|deception|intimidation|persuasion|performance)\s*(?:check)?'
        ]
        
        for pattern in ability_check_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                check_type = match.group(1).lower()
                mechanics.append({
                    "type": "ability_check",
                    "data": {"check_type": check_type}
                })
        
        # Parse combat rolls (e.g., "Roll a d20 for attack", "Roll initiative")
        combat_patterns = [
            r'roll\s+(?:a\s+)?(?:d20\s+)?(?:for\s+)?(?:an?\s+)?(?:attack|to\s+hit)',
            r'roll\s+(?:for\s+)?initiative',
            r'make\s+(?:an?\s+)?attack\s+roll'
        ]
        
        for pattern in combat_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                if "initiative" in match.group(0).lower():
                    roll_type = "initiative"
                else:
                    roll_type = "attack"
                mechanics.append({
                    "type": "combat_roll",
                    "data": {"roll_type": roll_type}
                })
        
        # Parse rest completion (e.g., "complete your long rest", "finish the short rest")
        rest_patterns = [
            r'(?:you\s+)?(?:complete|finish)(?:ed)?\s+(?:your\s+)?(?:the\s+)?(long|short)\s+rest',
            r'(?:your\s+)?(?:the\s+)?(long|short)\s+rest\s+(?:is\s+)?(?:completed|finished|over)',
            r'(?:you\s+)?(?:have\s+)?(?:rested|finished\s+resting)'
        ]
        
        for pattern in rest_patterns:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    rest_type = match.group(1).lower()
                else:
                    # Default to short rest if not specified
                    rest_type = "short"
                mechanics.append({
                    "type": "rest_complete",
                    "data": {"rest_type": rest_type}
                })
        
        return mechanics
    
    def _apply_damage(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Apply damage to character"""
        if self.db is None:
            logger.error("Database not available for damage application")
            return
        
        try:
            amount = data.get("amount", 0)
            if amount <= 0:
                return
            
            # Get character data
            character = self.db.characters.find_one({"character_id": character_id})
            if character is None:
                logger.error(f"Character not found: {character_id}")
                return
            
            # Apply damage to hit points
            hit_points = character.get("hit_points", {})
            current_hp = hit_points.get("current", 0)
            new_hp = max(0, current_hp - amount)  # HP can't go below 0
            
            # Update character with new HP
            self.db.characters.update_one(
                {"character_id": character_id},
                {"$set": {"hit_points.current": new_hp}}
            )
            
            logger.info(f"Applied {amount} damage to character {character_id}. HP: {current_hp} -> {new_hp}")
            
        except Exception as e:
            logger.error(f"Error applying damage: {e}")
    
    def _apply_healing(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Apply healing to character"""
        if self.db is None:
            logger.error("Database not available for healing application")
            return
        
        try:
            amount = data.get("amount", 0)
            if amount <= 0:
                return
            
            # Get character data
            character = self.db.characters.find_one({"character_id": character_id})
            if character is None:
                logger.error(f"Character not found: {character_id}")
                return
            
            # Apply healing to hit points
            hit_points = character.get("hit_points", {})
            current_hp = hit_points.get("current", 0)
            max_hp = hit_points.get("max", 0)
            new_hp = min(max_hp, current_hp + amount)  # HP can't exceed max
            
            # Update character with new HP
            self.db.characters.update_one(
                {"character_id": character_id},
                {"$set": {"hit_points.current": new_hp}}
            )
            
            logger.info(f"Applied {amount} healing to character {character_id}. HP: {current_hp} -> {new_hp}")
            
        except Exception as e:
            logger.error(f"Error applying healing: {e}")
    
    def _apply_condition(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Apply or remove a condition to/from character"""
        if self.db is None:
            logger.error("Database not available for condition application")
            return
        
        try:
            condition = data.get("condition", "")
            action = data.get("action", "add")
            
            if not condition:
                return
            
            # Get character data
            character = self.db.characters.find_one({"character_id": character_id})
            if character is None:
                logger.error(f"Character not found: {character_id}")
                return
            
            # Get current conditions
            conditions = character.get("conditions", [])
            
            if action == "add":
                if condition not in conditions:
                    conditions.append(condition)
                    # Update character with new condition
                    self.db.characters.update_one(
                        {"character_id": character_id},
                        {"$set": {"conditions": conditions}}
                    )
                    logger.info(f"Added condition {condition} to character {character_id}")
            
            elif action == "remove":
                if condition in conditions:
                    conditions.remove(condition)
                    # Update character with condition removed
                    self.db.characters.update_one(
                        {"character_id": character_id},
                        {"$set": {"conditions": conditions}}
                    )
                    logger.info(f"Removed condition {condition} from character {character_id}")
            
        except Exception as e:
            logger.error(f"Error applying condition: {e}")
    
    def _apply_resource_change(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Apply resource changes to character (spell slots, abilities, etc.)"""
        if self.db is None:
            logger.error("Database not available for resource change")
            return
        
        try:
            resource_type = data.get("resource_type", "")
            resource_key = data.get("resource_key", "")
            change_amount = data.get("change_amount", 0)
            
            if not resource_type or not resource_key:
                return
            
            # Get character data
            character = self.db.characters.find_one({"character_id": character_id})
            if character is None:
                logger.error(f"Character not found: {character_id}")
                return
            
            # Apply resource change based on type
            if resource_type == "spell_slot":
                spellcasting = character.get("spellcasting", {})
                slots = spellcasting.get("slots", {})
                if resource_key in slots:
                    if isinstance(slots[resource_key], dict):
                        current = slots[resource_key].get("available", 0)
                        new_value = max(0, current + change_amount)
                        slots[resource_key]["available"] = new_value
                    else:
                        # Simple numeric value
                        current = slots.get(resource_key, 0)
                        new_value = max(0, current + change_amount)
                        slots[resource_key] = new_value
                    
                    # Update character
                    self.db.characters.update_one(
                        {"character_id": character_id},
                        {"$set": {"spellcasting.slots": slots}}
                    )
                    logger.info(f"Updated spell slot {resource_key} for character {character_id}")
            
            elif resource_type == "feature_use":
                features = character.get("features", {})
                # Navigate to the specific feature and update its uses
                # This is a simplified implementation
                logger.info(f"Feature resource update for {resource_key} not fully implemented")
            
        except Exception as e:
            logger.error(f"Error applying resource change: {e}")
    
    def _apply_rest_mechanics(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Apply rest mechanics to character"""
        if self.db is None:
            logger.error("Database not available for rest mechanics")
            return
        
        try:
            rest_type = data.get("rest_type", "short")
            
            # Get character data
            character = self.db.characters.find_one({"character_id": character_id})
            if character is None:
                logger.error(f"Character not found: {character_id}")
                return
            
            if rest_type == "long":
                # Long rest: Restore all HP, HD, and spell slots
                hit_points = character.get("hit_points", {})
                max_hp = hit_points.get("max", 0)
                
                # Update character with full HP
                self.db.characters.update_one(
                    {"character_id": character_id},
                    {"$set": {"hit_points.current": max_hp}}
                )
                
                # Restore spell slots (if applicable)
                spellcasting = character.get("spellcasting", {})
                if "slots" in spellcasting:
                    restored_slots = {}
                    for level, slot_data in spellcasting["slots"].items():
                        if isinstance(slot_data, dict):
                            max_slots = slot_data.get("max", 0)
                            restored_slots[level] = {"max": max_slots, "available": max_slots}
                        else:
                            restored_slots[level] = slot_data
                    
                    self.db.characters.update_one(
                        {"character_id": character_id},
                        {"$set": {"spellcasting.slots": restored_slots}}
                    )
                
                # Clear most conditions
                conditions_to_keep = ["exhaustion"]  # Some conditions persist through long rest
                current_conditions = character.get("conditions", [])
                new_conditions = [c for c in current_conditions if c in conditions_to_keep]
                
                self.db.characters.update_one(
                    {"character_id": character_id},
                    {"$set": {"conditions": new_conditions}}
                )
                
                # Restore hit dice (simplified - restore half of total HD)
                level = character.get("level", 1)
                hit_dice_restored = max(1, level // 2)
                
                logger.info(f"Applied long rest mechanics to character {character_id}")
            
            else:  # short rest
                # Short rest: Limited healing and some resource recovery
                hit_points = character.get("hit_points", {})
                current_hp = hit_points.get("current", 0)
                max_hp = hit_points.get("max", 0)
                
                # If character has healing resources (like hit dice), use them
                # This is a simplified implementation
                if current_hp < max_hp:
                    # Basic healing for short rest (simplified)
                    healing = min(character.get("level", 1) * 2, max_hp - current_hp)
                    new_hp = current_hp + healing
                    
                    self.db.characters.update_one(
                        {"character_id": character_id},
                        {"$set": {"hit_points.current": new_hp}}
                    )
                
                logger.info(f"Applied short rest mechanics to character {character_id}")
            
        except Exception as e:
            logger.error(f"Error applying rest mechanics: {e}")
    
    def _record_ability_check(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Record an ability check request for the character"""
        check_type = data.get("check_type", "")
        if check_type:
            logger.info(f"Recorded ability check request: {check_type} for character {character_id}")
            
            # Store the pending check in the character's state
            if self.db is not None:
                self.db.characters.update_one(
                    {"character_id": character_id},
                    {"$set": {"pending_ability_check": check_type}}
                )
    
    def _record_combat_roll(self, state: AIGameState, character_id: str, data: Dict[str, Any]) -> None:
        """Record a combat roll request for the character"""
        roll_type = data.get("roll_type", "")
        if roll_type:
            logger.info(f"Recorded combat roll request: {roll_type} for character {character_id}")
            
            # Store the pending roll in the character's state
            if self.db is not None:
                self.db.characters.update_one(
                    {"character_id": character_id},
                    {"$set": {"pending_combat_roll": roll_type}}
                )

# Create a singleton instance
apply_mechanics_node = ApplyMechanicsNode()

# Function to use as node in graph
def process_apply_mechanics(state: AIGameState) -> AIGameState:
    """Apply mechanical effects from AI DM response"""
    return apply_mechanics_node(state)