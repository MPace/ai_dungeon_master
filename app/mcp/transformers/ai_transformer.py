"""
AI Prompt Transformer

This module provides the implementation of the AI prompt transformer,
which transforms the combined context into a format suitable for AI prompting.
"""

import logging
from typing import Dict, Any, List
from app.mcp.interfaces import IContextTransformer, BaseContext
from app.mcp.context_objects import AIPromptContext, PlayerContext, GameContext, MemoryContext

logger = logging.getLogger(__name__)

class AIPromptTransformer(IContextTransformer):
    """
    Transformer for AI prompting
    
    This transformer takes the combined context from various providers
    and transforms it into a format suitable for AI prompting.
    """
    
    def transform(self, context: BaseContext) -> BaseContext:
        """
        Transform the provided context into AI prompt context
        
        Args:
            context: The context to transform
            
        Returns:
            AIPromptContext: The transformed context
        """
        logger.info(f"Transforming context of type {type(context).__name__} for AI prompting")
        
        # If it's already an AIPromptContext, just return it
        if isinstance(context, AIPromptContext):
            return context
        
        # Initialize with empty values
        player_message = ""
        character_context = ""
        game_context_str = ""
        memory_context_str = ""
        game_state = "intro"
        conversation_history = []
        
        # Extract player context
        if isinstance(context, PlayerContext):
            character_context = self._format_character_context(context)
        
        # Extract game context
        elif isinstance(context, GameContext):
            game_context_str = self._format_game_context(context)
            game_state = context.game_state
        
        # Extract memory context
        elif isinstance(context, MemoryContext):
            memory_context_str = self._format_memory_context(context)
        
        # Generate system prompt based on game state
        system_prompt = self._create_system_prompt(game_state)
        
        # Get player message if available
        if hasattr(context, 'player_message'):
            player_message = context.player_message
            
        # Get conversation history if available
        if hasattr(context, 'history'):
            conversation_history = self._format_conversation_history(context.history)
        
        # Create AI prompt context
        ai_context = AIPromptContext(
            system_prompt=system_prompt,
            player_message=player_message,
            character_context=character_context,
            game_context=game_context_str,
            memory_context=memory_context_str,
            conversation_history=conversation_history
        )
        
        logger.info("Context transformed successfully for AI prompting")
        return ai_context
    
    def _format_character_context(self, context: PlayerContext) -> str:
        """Format character context for AI prompting"""
        if not context.character_data:
            return ""
        
        character_data = context.character_data
        
        # Format character information
        character_info = (
            f"## CHARACTER INFORMATION:\n"
            f"Name: {character_data.get('name', 'Unknown')}\n"
            f"Race: {character_data.get('race', 'Unknown')}\n"
            f"Class: {character_data.get('class', 'Unknown')}\n"
            f"Level: {character_data.get('level', 1)}\n"
            f"Background: {character_data.get('background', 'Unknown')}\n"
        )
        
        # Add abilities
        abilities_section = ""
        if character_data.get('abilities'):
            abilities_section = "Ability Scores:\n"
            for ability, score in character_data['abilities'].items():
                modifier = (score - 10) // 2
                sign = "+" if modifier >= 0 else ""
                abilities_section += f"- {ability.capitalize()}: {score} ({sign}{modifier})\n"
        
        # Add skills
        skills_section = ""
        if character_data.get('skills') and len(character_data['skills']) > 0:
            skills_section = "Skill Proficiencies:\n"
            for skill in character_data['skills']:
                skills_section += f"- {skill}\n"
        
        # Add description
        description_section = ""
        if character_data.get('description'):
            description_section = f"Description: {character_data['description']}\n"
        
        return f"{character_info}\n{abilities_section}\n{skills_section}\n{description_section}"
    
    def _format_game_context(self, context: GameContext) -> str:
        """Format game context for AI prompting"""
        # Format game state
        game_state_str = f"Current game state: {context.game_state}\n\n"
        
        # Format entities
        entities_str = "## IMPORTANT ENTITIES:\n"
        if context.entities:
            for name, data in context.entities.items():
                entity_type = data.get('type', 'unknown')
                description = data.get('description', 'No description available')
                entities_str += f"- {name} ({entity_type}): {description}\n"
        else:
            entities_str += "No important entities yet.\n"
        
        # Format environment
        environment_str = "## ENVIRONMENT:\n"
        if context.environment:
            for key, value in context.environment.items():
                environment_str += f"- {key}: {value}\n"
        else:
            environment_str += "No environment details available.\n"
        
        # Format player decisions
        decisions_str = ""
        if context.player_decisions:
            decisions_str = "## PLAYER DECISIONS:\n"
            # Show only the last few decisions to avoid overwhelming the context
            for decision in context.player_decisions[-3:]:
                decision_text = decision.get('decision', '')
                timestamp = decision.get('timestamp', '')
                decisions_str += f"- {decision_text} ({timestamp})\n"
        
        return f"{game_state_str}{entities_str}\n{environment_str}\n{decisions_str}"
    
    def _format_memory_context(self, context: MemoryContext) -> str:
        """Format memory context for AI prompting"""
        # Start with summary if available
        memory_str = ""
        if context.summary:
            memory_str = f"## SESSION SUMMARY:\n{context.summary}\n\n"
        
        # Add pinned memories
        if context.pinned_memories:
            memory_str += "## PINNED MEMORIES:\n"
            for memory in context.pinned_memories:
                content = memory.get('content', '')
                memory_type = memory.get('memory_type', 'unknown')
                memory_str += f"- ({memory_type}) {content}\n"
            memory_str += "\n"
        
        # Add relevant memories
        if context.memories:
            memory_str += "## RELEVANT MEMORIES:\n"
            for memory in context.memories:
                content = memory.get('content', '')
                memory_type = memory.get('memory_type', 'unknown')
                memory_str += f"- ({memory_type}) {content}\n"
        
        return memory_str
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format conversation history for AI prompting"""
        formatted = []
        
        # Process history entries
        for entry in history:
            role = "assistant" if entry.get("sender") == "dm" else "user"
            message = entry.get("message", "")
            
            formatted.append({
                "role": role,
                "content": message
            })
        
        return formatted
    
    def _create_system_prompt(self, game_state: str) -> str:
        """Create system prompt based on game state"""
        # Base prompt that applies to all states
        base_prompt = (
            "You are a seasoned Dungeon Master for a Dungeons & Dragons 5th Edition game, guiding a solo player through a rich fantasy world. "
            "Your role is to weave an immersive, engaging story, staying fully in character as a narrator and arbiter of the world. "
            "Respond with vivid descriptions, distinct NPC personalities, and a natural flow that draws the player into the adventure. "
            "Adhere strictly to D&D 5e rules, incorporating dice rolls (e.g., 'Roll a d20 for Perception') and mechanics only when necessary—blend them seamlessly into the narrative. "
            "When D&D 5e rules require a dice roll (e.g., Initiative, attack, skill check), prompt the player to roll the die (e.g., 'Roll a d20 for Initiative') and pause your response there. "
            "Do not guess, assume, or simulate the player's roll—wait for their next message with the result before advancing the story or resolving outcomes."
            "\n\n"
        )
        
        # State-specific prompts
        state_prompts = {
            "combat": (
                "The player is currently in combat. Narrate the scene with high stakes and visceral detail—blood, steel, and chaos. "
                "Manage combat turns: describe the enemy's action giving each enemy a turn if there are more than one, then prompt the player for their move. "
                "For dice rolls like initiative, attack rolls, or saves, always prompt the player to roll and stop there—do not assume or simulate the player's roll. "
                "Wait for the player to provide the result in their next message before continuing the combat sequence. "
                "Keep the pace fast and tense, but respect the player's agency over their rolls."
            ),
            "social": (
                "The player is in a social interaction. Portray NPCs with distinct personalities, motivations, and speech patterns. "
                "Respond to social approaches and charisma-based actions with appropriate reactions. "
                "Give NPCs clear voices, mannerisms, and attitudes that make them memorable. "
                "Allow for persuasion, deception, and intimidation attempts where appropriate, calling for dice rolls when needed."
            ),
            "exploration": (
                "The player is exploring. Describe the environment in rich detail with sensory information and interesting features that reward investigation. "
                "Offer clear directions and points of interest. Hint at possible secrets or hidden elements to create a sense of wonder and discovery. "
                "When perception, investigation, or other checks are needed, prompt for dice rolls and wait for player input."
            ),
            "intro": (
                "This is the beginning of a new adventure. Begin with the character already in an exciting, tense, or mysterious situation. "
                "Choose from a VARIETY of engaging scenarios such as: "
                "- In the middle of combat or a chase scene "
                "- Waking up in an unusual or dangerous place with no memory of how they got there "
                "- Witnessing something impossible or forbidden "
                "- Being mistaken for someone important or dangerous "
                "- Discovering a body or crime scene "
                "- Finding themselves in possession of a mysterious object "
                "- Caught in a natural disaster or magical catastrophe "
                "- Overhearing a secret conversation or plot "
                "- Being hunted or pursued by unknown forces "
                
                "CREATE A UNIQUE SCENARIO - DO NOT default to a burning tavern or any single formulaic opening. "
                "Consider the character's background and abilities when crafting this opening scene. "
                "Establish clear stakes and immediate tension while providing just enough context for the player to make decisions. "
                "Begin with vivid sensory details that pull the player into the action."
            )
        }
        
        # Get state-specific prompt, default to intro if not found
        state_prompt = state_prompts.get(game_state, state_prompts["intro"])
        
        return f"{base_prompt}{state_prompt}"