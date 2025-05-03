# app/langgraph_core/tools/validation_tools.py
"""
Validation Tools for AI Dungeon Master

These tools implement the validation logic for various player intents,
checking if actions are allowed based on character capabilities and game state.
"""
import logging
from typing import Dict, Any, List, Optional
import re

from app.extensions import get_db
from app.models.character import Character

logger = logging.getLogger(__name__)

class CombatValidatorTool:
    """Tool for validating combat-related actions (spells, attacks, features)"""
    
    def __init__(self):
        """Initialize combat validator"""
        self.db = get_db()
    
    def validate_spell_cast(self, character_id: str, spell_name: str, 
                         is_ritual: bool = False, 
                         game_state: str = "exploration") -> Dict[str, Any]:
        """
        Validate if a character can cast a specific spell
        
        Args:
            character_id: Character ID
            spell_name: Name of the spell to cast
            is_ritual: Whether the spell is being cast as a ritual
            game_state: Current game state
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Check if character can cast spells
            character_class = character_data.get('class', '').lower()
            spell_casting_classes = [
                'wizard', 'sorcerer', 'warlock', 'bard', 'cleric', 'druid', 
                'paladin', 'ranger', 'artificer'
            ]
            
            if character_class not in spell_casting_classes:
                return {
                    "status": False,
                    "reason": f"Your {character_class} cannot cast spells",
                    "details": None
                }
            
            # Check if the character has the spell
            spellcasting = character_data.get('spellcasting', {})
            spells = spellcasting.get('spells', [])
            
            # Normalize spell name for comparison
            spell_name_lower = spell_name.lower().strip()
            
            # Find the spell in the character's spell list
            spell_found = False
            spell_data = None
            
            for spell in spells:
                if spell.get('name', '').lower() == spell_name_lower:
                    spell_found = True
                    spell_data = spell
                    break
            
            if not spell_found:
                return {
                    "status": False,
                    "reason": f"You don't know the spell '{spell_name}'",
                    "details": None
                }
            
            # Check if spell slots are available (not needed if casting as a ritual)
            if not is_ritual:
                spell_level = spell_data.get('level', 0)
                
                # Check for spell slots
                if spell_level > 0:  # Not a cantrip
                    # Get available spell slots
                    spell_slots = spellcasting.get('slots', {})
                    available_slots = 0
                    
                    # Check for slots of the spell's level or higher
                    for level in range(spell_level, 10):
                        level_str = str(level)
                        if level_str in spell_slots:
                            slot_data = spell_slots[level_str]
                            if isinstance(slot_data, dict):
                                available = slot_data.get('available', 0)
                                available_slots += available
                            elif isinstance(slot_data, int):
                                available_slots += slot_data
                    
                    if available_slots <= 0:
                        return {
                            "status": False,
                            "reason": f"No spell slots available to cast {spell_name}",
                            "details": None
                        }
            else:  # Ritual casting
                # Check if the spell has the ritual tag
                if not spell_data.get('ritual', False):
                    return {
                        "status": False,
                        "reason": f"{spell_name} cannot be cast as a ritual",
                        "details": None
                    }
                
                # Check if the character can cast rituals
                can_cast_rituals = False
                if character_class in ['wizard', 'cleric', 'druid', 'bard']:
                    can_cast_rituals = True
                elif character_class == 'warlock':
                    # Check for Book of Ancient Secrets invocation
                    features = character_data.get('features', {})
                    invocations = features.get('eldritch_invocations', [])
                    if 'Book of Ancient Secrets' in invocations:
                        can_cast_rituals = True
                
                if not can_cast_rituals:
                    return {
                        "status": False,
                        "reason": f"Your {character_class} cannot cast spells as rituals",
                        "details": None
                    }
            
            # Check if in combat and spell casting is feasible
            if game_state == "combat":
                # Check for concentration if already concentrating
                # This would require tracking concentration in the game state
                pass
            
            # If we got here, the spell can be cast
            return {
                "status": True,
                "reason": None,
                "details": {
                    "spell_level": spell_data.get('level', 0),
                    "is_ritual": is_ritual,
                    "spell_data": spell_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating spell cast: {e}")
            return {
                "status": False,
                "reason": f"Error validating spell: {str(e)}",
                "details": None
            }
    
    def validate_weapon_attack(self, character_id: str, weapon_name: str,
                            game_state: str = "exploration") -> Dict[str, Any]:
        """
        Validate if a character can attack with a specific weapon
        
        Args:
            character_id: Character ID
            weapon_name: Name of the weapon
            game_state: Current game state
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Check if in combat
            if game_state != "combat":
                # Can still attack, but warn that not in combat
                pass
            
            # Check if the character has the weapon
            equipment = character_data.get('equipment', {})
            weapons = equipment.get('weapons', [])
            
            # Normalize weapon name for comparison
            weapon_name_lower = weapon_name.lower().strip()
            
            # Find the weapon in the character's equipment
            weapon_found = False
            weapon_data = None
            
            # Check for common weapon types if specific weapon not provided
            if not weapon_name:
                # Use first weapon in inventory
                if weapons and len(weapons) > 0:
                    weapon_data = weapons[0]
                    weapon_found = True
                    weapon_name = weapon_data.get('name', 'weapon')
            else:
                for weapon in weapons:
                    if weapon.get('name', '').lower() == weapon_name_lower:
                        weapon_found = True
                        weapon_data = weapon
                        break
            
            if not weapon_found:
                return {
                    "status": False,
                    "reason": f"You don't have {weapon_name} equipped",
                    "details": None
                }
            
            # Check for ammunition if ranged weapon
            weapon_type = weapon_data.get('type', '').lower()
            if 'ranged' in weapon_type:
                # Check for ammunition
                has_ammo = False
                
                # Check inventory for appropriate ammunition
                inventory = equipment.get('inventory', [])
                for item in inventory:
                    item_name = item.get('name', '').lower()
                    if 'arrow' in item_name or 'bolt' in item_name or 'bullet' in item_name:
                        quantity = item.get('quantity', 0)
                        if quantity > 0:
                            has_ammo = True
                            break
                
                if not has_ammo:
                    return {
                        "status": False,
                        "reason": f"You don't have ammunition for your {weapon_name}",
                        "details": None
                    }
            
            # If we got here, the attack is valid
            return {
                "status": True,
                "reason": None,
                "details": {
                    "weapon_data": weapon_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating weapon attack: {e}")
            return {
                "status": False,
                "reason": f"Error validating attack: {str(e)}",
                "details": None
            }
    
    def validate_feature_use(self, character_id: str, feature_name: str,
                          resource: str = "") -> Dict[str, Any]:
        """
        Validate if a character can use a specific feature
        
        Args:
            character_id: Character ID
            feature_name: Name of the feature
            resource: Resource to use (e.g., "1 use")
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Check if the character has the feature
            features = character_data.get('features', {})
            
            # Normalize feature name for comparison
            feature_name_lower = feature_name.lower().strip()
            
            # Look in different feature categories
            feature_found = False
            feature_data = None
            feature_category = None
            
            # Check class features
            class_features = features.get('class_features', [])
            for feature in class_features:
                if feature.get('name', '').lower() == feature_name_lower:
                    feature_found = True
                    feature_data = feature
                    feature_category = 'class_features'
                    break
            
            # Check racial features if not found in class features
            if not feature_found:
                racial_features = features.get('racial_features', [])
                for feature in racial_features:
                    if feature.get('name', '').lower() == feature_name_lower:
                        feature_found = True
                        feature_data = feature
                        feature_category = 'racial_features'
                        break
            
            # Check background features if still not found
            if not feature_found:
                background_features = features.get('background_features', [])
                for feature in background_features:
                    if feature.get('name', '').lower() == feature_name_lower:
                        feature_found = True
                        feature_data = feature
                        feature_category = 'background_features'
                        break
            
            if not feature_found:
                return {
                    "status": False,
                    "reason": f"You don't have the feature '{feature_name}'",
                    "details": None
                }
            
            # Check if the feature has limited uses and if any are available
            uses = feature_data.get('uses', {})
            max_uses = uses.get('max', 0)
            
            if max_uses > 0:
                current_uses = uses.get('current', 0)
                
                if current_uses <= 0:
                    return {
                        "status": False,
                        "reason": f"No uses of {feature_name} remaining",
                        "details": None
                    }
            
            # If we got here, the feature can be used
            return {
                "status": True,
                "reason": None,
                "details": {
                    "feature_data": feature_data,
                    "feature_category": feature_category
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating feature use: {e}")
            return {
                "status": False,
                "reason": f"Error validating feature: {str(e)}",
                "details": None
            }
    
    def _load_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load character data from the database"""
        if self.db is None:
            logger.error("Database connection not available")
            return None
        
        try:
            # Query the database for the character
            character_doc = self.db.characters.find_one({"character_id": character_id})
            
            if not character_doc:
                logger.warning(f"Character not found: {character_id}")
                return None
            
            # If we have a Character object, convert to dict
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
            
        except Exception as e:
            logger.error(f"Error loading character data: {e}")
            return None


class ActionValidatorTool:
    """Tool for validating skill checks and ability-based actions"""
    
    def __init__(self):
        """Initialize action validator"""
        self.db = get_db()
    
    def validate_action(self, character_id: str, action: str, skill: str = "") -> Dict[str, Any]:
        """
        Validate if a character can perform a specific action/skill check
        
        Args:
            character_id: Character ID
            action: Action to perform
            skill: Skill to use (if applicable)
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Map common actions to skills
            action_skill_map = {
                "persuade": "persuasion",
                "intimidate": "intimidation",
                "deceive": "deception",
                "stealth": "stealth",
                "hide": "stealth",
                "investigate": "investigation",
                "insight": "insight",
                "perception": "perception",
                "climb": "athletics",
                "jump": "athletics",
                "acrobatics": "acrobatics"
            }
            
            # Normalize action and skill
            action_lower = action.lower().strip()
            skill_lower = skill.lower().strip() if skill else ""
            
            # If no skill provided, try to derive from action
            if not skill_lower and action_lower in action_skill_map:
                skill_lower = action_skill_map[action_lower]
            
            # Get character proficiencies
            proficiencies = character_data.get('proficiencies', {})
            skills = proficiencies.get('skills', [])
            
            # Check if character is proficient in the skill
            is_proficient = skill_lower in skills
            
            # Determine ability modifier for the skill
            abilities = character_data.get('abilities', {})
            ability_modifier = 0
            
            # Map skills to abilities
            skill_ability_map = {
                "athletics": "strength",
                "acrobatics": "dexterity",
                "sleight_of_hand": "dexterity",
                "stealth": "dexterity",
                "arcana": "intelligence",
                "history": "intelligence",
                "investigation": "intelligence",
                "nature": "intelligence",
                "religion": "intelligence",
                "animal_handling": "wisdom",
                "insight": "wisdom",
                "medicine": "wisdom",
                "perception": "wisdom",
                "survival": "wisdom",
                "deception": "charisma",
                "intimidation": "charisma",
                "performance": "charisma",
                "persuasion": "charisma"
            }
            
            # Get the ability for this skill
            ability = skill_ability_map.get(skill_lower, "dexterity")
            ability_score = abilities.get(ability, 10)
            
            # Calculate modifier
            ability_modifier = (ability_score - 10) // 2
            
            # Actions are almost always valid, but we return proficiency info
            return {
                "status": True,
                "reason": None,
                "details": {
                    "skill": skill_lower or action_lower,
                    "ability": ability,
                    "is_proficient": is_proficient,
                    "ability_modifier": ability_modifier
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating action: {e}")
            return {
                "status": False,
                "reason": f"Error validating action: {str(e)}",
                "details": None
            }
    
    def _load_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load character data from the database"""
        if self.db is None:
            logger.error("Database connection not available")
            return None
        
        try:
            # Query the database for the character
            character_doc = self.db.characters.find_one({"character_id": character_id})
            
            if not character_doc:
                logger.warning(f"Character not found: {character_id}")
                return None
            
            # If we have a Character object, convert to dict
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
            
        except Exception as e:
            logger.error(f"Error loading character data: {e}")
            return None


class ItemValidatorTool:
    """Tool for validating item use and management"""
    
    def __init__(self):
        """Initialize item validator"""
        self.db = get_db()
    
    def validate_item_use(self, character_id: str, item_name: str) -> Dict[str, Any]:
        """
        Validate if a character can use a specific item
        
        Args:
            character_id: Character ID
            item_name: Name of the item to use
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Check if the character has the item
            equipment = character_data.get('equipment', {})
            inventory = equipment.get('inventory', [])
            
            # Normalize item name for comparison
            item_name_lower = item_name.lower().strip()
            
            # Find the item in the character's inventory
            item_found = False
            item_data = None
            
            for item in inventory:
                if item.get('name', '').lower() == item_name_lower:
                    item_found = True
                    item_data = item
                    break
            
            if not item_found:
                return {
                    "status": False,
                    "reason": f"You don't have {item_name} in your inventory",
                    "details": None
                }
            
            # Check if the item has charges/uses and if any are available
            charges = item_data.get('charges', {})
            max_charges = charges.get('max', 0)
            
            if max_charges > 0:
                current_charges = charges.get('current', 0)
                
                if current_charges <= 0:
                    return {
                        "status": False,
                        "reason": f"No charges remaining on {item_name}",
                        "details": None
                    }
            
            # Check quantity
            quantity = item_data.get('quantity', 1)
            if quantity <= 0:
                return {
                    "status": False,
                    "reason": f"You don't have any {item_name} remaining",
                    "details": None
                }
            
            # If we got here, the item can be used
            return {
                "status": True,
                "reason": None,
                "details": {
                    "item_data": item_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating item use: {e}")
            return {
                "status": False,
                "reason": f"Error validating item: {str(e)}",
                "details": None
            }
    
    def validate_item_management(self, character_id: str, item_name: str,
                              action_type: str) -> Dict[str, Any]:
        """
        Validate item management actions (take, drop, equip, unequip)
        
        Args:
            character_id: Character ID
            item_name: Name of the item
            action_type: Type of action ('take', 'drop', 'equip', 'unequip', 'inventory')
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Check action type
            if action_type not in ["take", "drop", "equip", "unequip", "inventory"]:
                return {
                    "status": False,
                    "reason": f"Invalid item action: {action_type}",
                    "details": None
                }
            
            # For inventory check, always valid
            if action_type == "inventory":
                return {
                    "status": True,
                    "reason": None,
                    "details": {
                        "action_type": "inventory"
                    }
                }
            
            # Normalize item name for comparison
            item_name_lower = item_name.lower().strip()
            
            # Get character equipment
            equipment = character_data.get('equipment', {})
            inventory = equipment.get('inventory', [])
            equipped_items = {}
            
            # Build equipped items dictionary
            for slot, item in equipment.items():
                if slot not in ['inventory', 'weapons', 'armor']:
                    equipped_items[slot] = item
            
            # Handle based on action type
            if action_type == "drop" or action_type == "unequip":
                # Check if character has the item
                item_found = False
                item_data = None
                
                # Check inventory
                for item in inventory:
                    if item.get('name', '').lower() == item_name_lower:
                        item_found = True
                        item_data = item
                        break
                
                # Check equipped items if not found in inventory
                if not item_found:
                    for slot, item in equipped_items.items():
                        if isinstance(item, dict) and item.get('name', '').lower() == item_name_lower:
                            item_found = True
                            item_data = item
                            break
                
                if not item_found:
                    return {
                        "status": False,
                        "reason": f"You don't have {item_name}",
                        "details": None
                    }
                
                return {
                    "status": True,
                    "reason": None,
                    "details": {
                        "action_type": action_type,
                        "item_data": item_data
                    }
                }
                
            elif action_type == "equip":
                # Check if character has the item in inventory
                item_found = False
                item_data = None
                
                for item in inventory:
                    if item.get('name', '').lower() == item_name_lower:
                        item_found = True
                        item_data = item
                        break
                
                if not item_found:
                    return {
                        "status": False,
                        "reason": f"You don't have {item_name} in your inventory",
                        "details": None
                    }
                
                # Determine item type and equipment slot
                item_type = item_data.get('type', 'miscellaneous').lower()
                slot = None
                
                if 'weapon' in item_type:
                    slot = 'weapon'
                elif 'armor' in item_type:
                    armor_type = item_data.get('armor_type', 'light').lower()
                    if armor_type == 'shield':
                        slot = 'shield'
                    else:
                        slot = 'armor'
                elif item_type in ['ring', 'amulet', 'cloak', 'boots', 'gloves', 'belt', 'helmet']:
                    slot = item_type
                
                if not slot:
                    return {
                        "status": False,
                        "reason": f"{item_name} cannot be equipped",
                        "details": None
                    }
                
                return {
                    "status": True,
                    "reason": None,
                    "details": {
                        "action_type": action_type,
                        "item_data": item_data,
                        "slot": slot
                    }
                }
                
            elif action_type == "take":
                # Taking item from environment - always valid, but narrative may limit
                return {
                    "status": True,
                    "reason": None,
                    "details": {
                        "action_type": action_type,
                        "item_name": item_name
                    }
                }
            
            # Default case
            return {
                "status": True,
                "reason": None,
                "details": {
                    "action_type": action_type,
                    "item_name": item_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating item management: {e}")
            return {
                "status": False,
                "reason": f"Error validating item action: {str(e)}",
                "details": None
            }
    
    def _load_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load character data from the database"""
        if self.db is None:
            logger.error("Database connection not available")
            return None
        
        try:
            # Query the database for the character
            character_doc = self.db.characters.find_one({"character_id": character_id})
            
            if not character_doc:
                logger.warning(f"Character not found: {character_id}")
                return None
            
            # If we have a Character object, convert to dict
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
            
        except Exception as e:
            logger.error(f"Error loading character data: {e}")
            return None


class RestFeasibilityCheckTool:
    """Tool for validating rest actions"""
    
    def __init__(self):
        """Initialize rest validator"""
        self.db = get_db()
    
    def validate_rest(self, character_id: str, location_id: Optional[str], 
                    duration: str, game_state: str,
                    narrative_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if a character can rest in the current location and situation
        
        Args:
            character_id: Character ID
            location_id: Current location ID
            duration: Rest duration ('short' or 'long')
            game_state: Current game state
            narrative_state: Current narrative state
            
        Returns:
            Validation result
        """
        try:
            # Load the character data
            character_data = self._load_character(character_id)
            if not character_data:
                return {
                    "status": False,
                    "reason": "Character not found",
                    "details": None
                }
            
            # Cannot rest in combat
            if game_state == "combat":
                return {
                    "status": False,
                    "reason": "You cannot rest while in combat",
                    "details": None
                }
            
            # Check if location allows resting
            if location_id:
                # Check location_states in narrative_state
                location_states = narrative_state.get('location_states', {})
                if location_id in location_states:
                    location_state = location_states[location_id]
                    
                    # Check for rest restrictions
                    if 'no_rest' in location_state or 'unsafe' in location_state:
                        return {
                            "status": False,
                            "reason": "This location is too dangerous for resting",
                            "details": None
                        }
            
            # Check environment state for time-based restrictions
            environment_state = narrative_state.get('environment_state', {})
            current_day_phase = environment_state.get('current_day_phase', '')
            
            if duration == "long" and current_day_phase not in ['Evening', 'Night']:
                # Long rest typically takes 8 hours and is normally taken at night
                # This isn't a hard restriction, just a warning in the response
                pass
            
            # Get character's current hit points
            hit_points = character_data.get('hit_points', {})
            current_hp = hit_points.get('current', 0)
            max_hp = hit_points.get('max', 0)
            
            # If already at full health, inform player
            if current_hp >= max_hp and duration == "short":
                # We'll still allow the rest, but inform the player they're at full health
                pass
            
            # Rest is possible
            return {
                "status": True,
                "reason": None,
                "details": {
                    "duration": duration,
                    "location_id": location_id,
                    "current_hp": current_hp,
                    "max_hp": max_hp
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating rest: {e}")
            return {
                "status": False,
                "reason": f"Error validating rest: {str(e)}",
                "details": None
            }
    
    def _load_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load character data from the database"""
        if self.db is None:
            logger.error("Database connection not available")
            return None
        
        try:
            # Query the database for the character
            character_doc = self.db.characters.find_one({"character_id": character_id})
            
            if not character_doc:
                logger.warning(f"Character not found: {character_id}")
                return None
            
            # If we have a Character object, convert to dict
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
            
        except Exception as e:
            logger.error(f"Error loading character data: {e}")
            return None