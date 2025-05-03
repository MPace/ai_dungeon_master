# app/langgraph_core/nodes/ai_dm_node.py
"""
AI DM Node for LangGraph

This node generates the AI Dungeon Master's response based on player input,
game state, memory context, and narrative context.
"""
import logging
from typing import Dict, Any, List, Optional
import json
import os

from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.narrative_tools import GetNarrativeContextTool
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class AIDMNode:
    """Node for generating AI Dungeon Master responses in the LangGraph"""
    
    def __init__(self):
        """Initialize AI DM node with necessary tools and services"""
        self.narrative_context_tool = GetNarrativeContextTool()
        self.ai_service = AIService()
        
        # Token budget for different context components
        self.total_token_budget = 4096  # Total available tokens
        self.system_prompt_tokens = 800  # Approximate tokens for system prompt
        self.narrative_context_tokens = 800  # Budget for narrative context
        self.memory_context_tokens = 1500  # Budget for memory context
        self.player_input_tokens = 200  # Budget for player input
        self.buffer_tokens = 100  # Buffer for safety
    
    def __call__(self, state: AIGameState) -> AIGameState:
        """
        Generate the AI Dungeon Master's response
        
        Args:
            state: Current game state
            
        Returns:
            Updated state with DM response
        """
        try:
            # Extract player input and intent data
            player_input = state.get("player_input", "")
            intent_data = state.get("intent_data", {})
            validation_result = state.get("validation_result", {})
            
            # Check if validation failed but we need to continue
            validation_failed = validation_result and not validation_result.get("status", True)
            
            # Get narrative context
            narrative_context = self.narrative_context_tool.get_narrative_context(state)
            
            # Perform token budgeting
            memory_context = self._get_memory_context(state)
            
            # Assemble the prompt with budgeted context
            prompt_template = self._assemble_prompt(
                state=state,
                narrative_context=narrative_context,
                memory_context=memory_context,
                validation_failed=validation_failed
            )
            
            # Prepare request parameters
            conversation_history = self._get_conversation_history(state)
            character_data = self._get_character_data(state)
            game_state = state.get("game_state", "exploration")
            
            # Call the AI service to generate the response
            result = self.ai_service.generate_response(
                player_message=player_input,
                conversation_history=conversation_history,
                character_data=character_data,
                game_state=game_state
            )
            
            # Extract the response text
            response_text = result.response_text if hasattr(result, 'response_text') else str(result)
            
            # Update state with the response
            state["dm_response"] = response_text
            
            logger.info(f"Generated DM response of {len(response_text)} chars")
            
            return state
            
        except Exception as e:
            logger.error(f"Error in AI DM node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Provide a fallback response
            state["dm_response"] = "The Dungeon Master pauses for a moment. (An error occurred while generating the response.)"
            return state
    
    def _get_memory_context(self, state: AIGameState) -> Dict[str, str]:
        """
        Retrieve and format memory context for the prompt
        
        Args:
            state: Current game state
            
        Returns:
            Dict with memory context sections
        """
        # This would normally be populated by the memory system
        # For now, use the tracked_narrative_state to build a simple context
        
        character_id = state.get("current_character_id")
        session_id = state.get("current_session_id")
        
        # Initialize empty context
        memory_context = {
            "history": "",
            "relevant_docs": "",
            "entities": ""
        }
        
        # Try to get memory context from the state if it exists
        if "memory_context" in state and state["memory_context"] is not None:
            return state["memory_context"]
        
        # Get conversation history from the state's tracked_narrative_state
        narrative_state = state.get("tracked_narrative_state", {})
        
        # Format memory context using the memory service
        from app.services.memory_service_enhanced import EnhancedMemoryService
        memory_service = EnhancedMemoryService()
        
        # Get current message
        current_message = state.get("player_input", "")
        
        # Build memory context
        if memory_service and session_id:
            formatted_context = memory_service.build_memory_context(
                current_message=current_message,
                session_id=session_id,
                character_id=character_id,
                max_tokens=self.memory_context_tokens
            )
            
            # Parse the formatted context into sections
            sections = formatted_context.split("##")
            for section in sections:
                if "RELEVANT MEMORIES:" in section:
                    memory_context["relevant_docs"] = section.replace("RELEVANT MEMORIES:", "").strip()
                elif "CONVERSATION HISTORY:" in section:
                    memory_context["history"] = section.replace("CONVERSATION HISTORY:", "").strip()
                elif "CAMPAIGN SUMMARY:" in section:
                    memory_context["entities"] = section.replace("CAMPAIGN SUMMARY:", "").strip()
                elif "PINNED MEMORIES:" in section:
                    # Add pinned memories to relevant docs with priority
                    pinned = section.replace("PINNED MEMORIES:", "").strip()
                    memory_context["relevant_docs"] = pinned + "\n\n" + memory_context["relevant_docs"]
        
        return memory_context
    
    def _assemble_prompt(self, state: AIGameState, 
                      narrative_context: Dict[str, Any],
                      memory_context: Dict[str, str],
                      validation_failed: bool) -> str:
        """
        Assemble the prompt for the AI DM
        
        Args:
            state: Current game state
            narrative_context: Narrative context from the NarrativeContextTool
            memory_context: Memory context from the memory system
            validation_failed: Whether validation failed
            
        Returns:
            Assembled prompt template
        """
        # Get current game state and intent
        game_state = state.get("game_state", "exploration")
        intent_data = state.get("intent_data", {})
        intent = intent_data.get("intent", "general")
        slots = intent_data.get("slots", {})
        
        # Get character data
        character_id = state.get("current_character_id")
        character_data = self._get_character_data(state)
        
        # Base system prompt
        system_prompt = (
            "You are a seasoned Dungeon Master for a Dungeons & Dragons 5th Edition game, "
            "guiding a solo player through a rich fantasy world. Your role is to weave an "
            "immersive, engaging story, staying fully in character as a narrator and arbiter "
            "of the world. Respond with vivid descriptions, distinct NPC personalities, and "
            "a natural flow that draws the player into the adventure. Adhere strictly to D&D 5e "
            "rules, incorporating dice rolls (e.g., 'Roll a d20 for Perception') and mechanics "
            "only when necessary—blend them seamlessly into the narrative. When D&D 5e rules "
            "require a dice roll (e.g., Initiative, attack, skill check), prompt the player to "
            "roll the die (e.g., 'Roll a d20 for Initiative') and pause your response there. "
            "Do not guess, assume, or simulate the player's roll—wait for their next message "
            "with the result before advancing the story or resolving outcomes.\n\n"
            
            "Format your response:\n"
            "- Use bold for important people, places, and items\n"
            "- Break long text into paragraphs every 3–4 sentences\n"
            "- Use Markdown style formatting\n"
            "- Avoid repeating prior information\n\n"
        )
        
        # Add state-specific instructions
        if game_state == "combat":
            system_prompt += (
                "The player is currently in combat. Narrate the scene with high stakes "
                "and visceral detail—blood, steel, and chaos. Manage combat turns: "
                "describe the enemy's action, then prompt the player for their move. "
                "For dice rolls like initiative, attack rolls, or saves, always prompt "
                "the player to roll and stop there—do not assume or simulate the player's roll. "
                "Wait for the player to provide the result in their next message before "
                "continuing the combat sequence. Keep the pace fast and tense, but respect "
                "the player's agency over their rolls.\n\n"
            )
        elif game_state == "social":
            system_prompt += (
                "The player is in a social interaction. Portray NPCs with distinct "
                "personalities, motivations, and speech patterns. Respond to social "
                "approaches and charisma-based actions with appropriate reactions. "
                "Give NPCs clear voices, mannerisms, and attitudes that make them memorable. "
                "Allow for persuasion, deception, and intimidation attempts where appropriate, "
                "calling for dice rolls when needed.\n\n"
            )
        elif game_state == "exploration":
            system_prompt += (
                "The player is exploring. Describe the environment in rich detail with "
                "sensory information and interesting features that reward investigation. "
                "Offer clear directions and points of interest. Hint at possible secrets "
                "or hidden elements to create a sense of wonder and discovery. When perception, "
                "investigation, or other checks are needed, prompt for dice rolls and wait "
                "for player input.\n\n"
            )
        elif game_state == "intro":
            system_prompt += (
                "This is the beginning of a new adventure. Begin with the character already "
                "in an exciting, tense, or mysterious situation. Choose from a VARIETY of "
                "engaging scenarios such as: in the middle of combat or a chase scene, "
                "waking up in an unusual or dangerous place, witnessing something impossible "
                "or forbidden, being mistaken for someone important, discovering a body or "
                "crime scene, finding a mysterious object, caught in a catastrophe, "
                "overhearing a secret conversation, or being hunted by unknown forces. "
                "CREATE A UNIQUE SCENARIO - DO NOT default to a burning tavern or any single "
                "formulaic opening. Consider the character's background and abilities when "
                "crafting this opening scene. Establish clear stakes and immediate tension "
                "while providing just enough context for the player to make decisions. "
                "Begin with vivid sensory details that pull the player into the action.\n\n"
            )
        
        # Add character information
        character_info = "## CHARACTER INFORMATION:\n"
        if character_data:
            character_info += (
                f"Name: {character_data.get('name', 'Unknown')}\n"
                f"Race: {character_data.get('race', 'Unknown')}\n"
                f"Class: {character_data.get('class', character_data.get('character_class', 'Unknown'))}\n"
                f"Level: {character_data.get('level', 1)}\n"
                f"Background: {character_data.get('background', 'Unknown')}\n"
            )
            
            # Add abilities if available
            abilities = character_data.get('abilities', {})
            if abilities:
                character_info += "Ability Scores:\n"
                for ability, score in abilities.items():
                    modifier = (score - 10) // 2
                    sign = "+" if modifier >= 0 else ""
                    character_info += f"- {ability.capitalize()}: {score} ({sign}{modifier})\n"
            
            # Add skills if available
            skills = character_data.get('skills', [])
            if skills:
                character_info += "Skill Proficiencies:\n"
                for skill in skills:
                    character_info += f"- {skill}\n"
            
            # Add description if available
            description = character_data.get('description', '')
            if description:
                character_info += f"Description: {description}\n"
        else:
            character_info += "No character data available.\n"
        
        # Add narrative context
        narrative_context_text = "## NARRATIVE CONTEXT:\n"
        
        # Location description
        location_description = narrative_context.get("location_description")
        if location_description:
            narrative_context_text += f"Current Location: {location_description}\n\n"
        
        # Time information
        time_info = narrative_context.get("current_time")
        if time_info:
            narrative_context_text += f"Current Time: {time_info.get('datetime', 'Unknown')} ({time_info.get('day_phase', 'Unknown')})\n\n"
        
        # Environmental conditions
        env_conditions = narrative_context.get("environmental_conditions", [])
        if env_conditions:
            narrative_context_text += "Environmental Conditions:\n"
            for condition in env_conditions:
                narrative_context_text += f"- {condition}\n"
            narrative_context_text += "\n"
        
        # Active quests
        active_quests = narrative_context.get("active_quests", [])
        if active_quests:
            narrative_context_text += "Active Quests:\n"
            for quest in active_quests:
                narrative_context_text += f"- {quest.get('name', 'Unknown Quest')}: {quest.get('objective', '')}\n"
            narrative_context_text += "\n"
        
        # Add validation failure information if applicable
        if validation_failed:
            validation_result = state.get("validation_result", {})
            reason = validation_result.get("reason", "Action not possible")
            narrative_context_text += f"## ACTION FAILED:\n{reason}\n\n"
        
        # Combine all sections
        full_prompt = (
            f"{system_prompt}\n\n"
            f"{character_info}\n\n"
            f"{narrative_context_text}\n\n"
        )
        
        # Add memory context sections
        if memory_context.get("history"):
            full_prompt += f"## CONVERSATION HISTORY:\n{memory_context['history']}\n\n"
        
        if memory_context.get("entities"):
            full_prompt += f"## KNOWN ENTITIES (CONVERSATIONAL):\n{memory_context['entities']}\n\n"
        
        if memory_context.get("relevant_docs"):
            full_prompt += f"## RELEVANT KNOWLEDGE & EVENTS:\n{memory_context['relevant_docs']}\n\n"
        
        # Add current player input
        full_prompt += f"## PLAYER INPUT:\n{state.get('player_input', '')}\n\n"
        
        return full_prompt
    
    def _get_conversation_history(self, state: AIGameState) -> List[Dict[str, str]]:
        """
        Get conversation history from state
        
        Args:
            state: Current game state
            
        Returns:
            List of conversation messages
        """
        # Get session ID to retrieve history
        session_id = state.get("current_session_id")
        if not session_id:
            return []
        
        # Try to get history from database
        from app.extensions import get_db
        db = get_db()
        
        if db is None:
            return []
        
        try:
            # Get session document
            session_doc = db.sessions.find_one({"session_id": session_id})
            
            if not session_doc or "history" not in session_doc:
                return []
            
            # Convert session history to format expected by AI service
            history = []
            for entry in session_doc["history"]:
                sender = entry.get("sender", "")
                message = entry.get("message", "")
                
                if sender and message:
                    history.append({
                        "sender": "dm" if sender == "dm" else "player",
                        "message": message
                    })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _get_character_data(self, state: AIGameState) -> Optional[Dict[str, Any]]:
        """
        Get character data from database
        
        Args:
            state: Current game state
            
        Returns:
            Dict or None: Character data if found
        """
        character_id = state.get("current_character_id")
        if not character_id:
            return None
        
        # Try to get character from database
        from app.extensions import get_db
        db = get_db()
        
        if db is None:
            return None
        
        try:
            # Query for character
            character_doc = db.characters.find_one({"character_id": character_id})
            
            if not character_doc:
                return None
            
            # Convert to dict if it's an object
            if hasattr(character_doc, 'to_dict'):
                return character_doc.to_dict()
            
            return character_doc
            
        except Exception as e:
            logger.error(f"Error getting character data: {e}")
            return None

# Create a singleton instance
ai_dm_node = AIDMNode()

# Function to use as node in graph
def process_ai_dm(state: AIGameState) -> AIGameState:
    """Generate the AI Dungeon Master's response"""
    return ai_dm_node(state)