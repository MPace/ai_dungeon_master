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
import tiktoken

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.narrative_tools import GetNarrativeContextTool

logger = logging.getLogger(__name__)

class AIDMNode:
    """Node for generating AI Dungeon Master responses in the LangGraph"""
    
    def __init__(self, conversation_memory=None, vector_memory=None, entity_memory=None):
        """Initialize AI DM node with necessary tools, services, and memory components"""
        self.narrative_context_tool = GetNarrativeContextTool()
        
        # Store memory instances passed from the manager
        self.conversation_memory = conversation_memory
        self.vector_memory = vector_memory
        self.entity_memory = entity_memory
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.8,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize token encoder for accurate counting
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        
        # Token budget for different context components
        self.total_token_budget = 8192  # GPT-4 context window
        self.response_reserve = 1000     # Reserve for the response
        self.system_prompt_tokens = 800  # Approximate tokens for system prompt
        self.character_info_tokens = 400 # Budget for character information
        self.narrative_context_tokens = 600  # Budget for narrative context
        self.player_input_tokens = 200   # Budget for player input
        
        # Calculate remaining budget for memory context
        self.memory_context_tokens = (
            self.total_token_budget 
            - self.response_reserve 
            - self.system_prompt_tokens 
            - self.character_info_tokens
            - self.narrative_context_tokens
            - self.player_input_tokens
        )
    
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
            
            # Get memory context from LangChain memory components
            memory_context = self._get_memory_context_from_langchain(state)
            
            # Assemble the prompt with budgeted context
            prompt_template = self._assemble_prompt(
                state=state,
                narrative_context=narrative_context,
                memory_context=memory_context,
                validation_failed=validation_failed
            )
            
            # Create prompt template for LangChain
            chat_prompt = ChatPromptTemplate.from_template(prompt_template)
            
            # Format the prompt with the current player input
            formatted_prompt = chat_prompt.format_messages(player_input=player_input)
            
            # Call the LLM using LangChain
            response = self.llm.invoke(formatted_prompt)
            
            # Extract the response content
            response_text = response.content
            
            # Update entity memory after getting the response
            if self.entity_memory:
                try:
                    self.entity_memory.save_context(
                        inputs={'player_input': player_input},
                        outputs={'output': response_text}
                    )
                except Exception as e:
                    logger.error(f"Error updating entity memory: {e}")
            
            # If structured output is enabled, parse it
            if self._should_use_structured_output(state):
                response_text, mechanics_data = self._parse_structured_response(response_text)
                
                # Store parsed mechanics data in state for ApplyMechanicsNode
                state["parsed_mechanics"] = mechanics_data
            
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
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in a text string using tiktoken"""
        return len(self.encoder.encode(text))
    
    def _get_memory_context_from_langchain(self, state: AIGameState) -> Dict[str, str]:
        """
        Retrieve memory context from LangChain memory components
        
        Args:
            state: Current game state
            
        Returns:
            Dict with memory context sections
        """
        memory_context = {
            "history": "",
            "relevant_docs": "",
            "entities": ""
        }
        
        player_input = state.get("player_input", "")
        
        # Get conversation history from ConversationBufferWindowMemory
        if self.conversation_memory:
            try:
                history_vars = self.conversation_memory.load_memory_variables({'player_input': player_input})
                memory_context["history"] = history_vars.get("history", "")
            except Exception as e:
                logger.error(f"Error loading conversation memory: {e}")
        
        # Get relevant documents from VectorStoreRetrieverMemory
        if self.vector_memory:
            try:
                doc_vars = self.vector_memory.load_memory_variables({'player_input': player_input})
                memory_context["relevant_docs"] = doc_vars.get("relevant_docs", "")
            except Exception as e:
                logger.error(f"Error loading vector memory: {e}")
        
        # Get entity information from EntityMemory
        if self.entity_memory:
            try:
                entity_vars = self.entity_memory.load_memory_variables({'player_input': player_input})
                memory_context["entities"] = entity_vars.get("entities", "")
            except Exception as e:
                logger.error(f"Error loading entity memory: {e}")
        
        return memory_context
    
    def _apply_token_budget(self, memory_context: Dict[str, str], budget: int) -> Dict[str, str]:
        """
        Apply token budget to memory context, trimming as needed
        
        Args:
            memory_context: Raw memory context
            budget: Token budget for memory context
            
        Returns:
            Trimmed memory context
        """
        # Count tokens in each section
        history_tokens = self._count_tokens(memory_context["history"])
        docs_tokens = self._count_tokens(memory_context["relevant_docs"])
        entities_tokens = self._count_tokens(memory_context["entities"])
        
        total_tokens = history_tokens + docs_tokens + entities_tokens
        
        # If within budget, return as-is
        if total_tokens <= budget:
            return memory_context
        
        # Apply trimming in priority order
        trimmed_context = memory_context.copy()
        
        # First, trim relevant_docs (least important)
        if total_tokens > budget:
            # Calculate how many tokens we need to trim
            tokens_to_trim = total_tokens - budget
            
            # Trim from the end of relevant_docs
            if docs_tokens > tokens_to_trim:
                docs_sentences = memory_context["relevant_docs"].split('. ')
                while docs_tokens > tokens_to_trim and len(docs_sentences) > 1:
                    docs_sentences.pop()
                    trimmed_docs = '. '.join(docs_sentences) + '.' if docs_sentences else ''
                    docs_tokens = self._count_tokens(trimmed_docs)
                    trimmed_context["relevant_docs"] = trimmed_docs
            else:
                trimmed_context["relevant_docs"] = ""
                tokens_to_trim -= docs_tokens
                
                # Next, trim entities
                if entities_tokens > tokens_to_trim:
                    entities_sentences = memory_context["entities"].split('. ')
                    while entities_tokens > tokens_to_trim and len(entities_sentences) > 1:
                        entities_sentences.pop()
                        trimmed_entities = '. '.join(entities_sentences) + '.' if entities_sentences else ''
                        entities_tokens = self._count_tokens(trimmed_entities)
                        trimmed_context["entities"] = trimmed_entities
                else:
                    trimmed_context["entities"] = ""
                    tokens_to_trim -= entities_tokens
                    
                    # Finally, trim history (most important, so last resort)
                    if history_tokens > tokens_to_trim:
                        history_lines = memory_context["history"].split('\n')
                        while history_tokens > tokens_to_trim and len(history_lines) > 1:
                            history_lines.pop(0)  # Remove oldest messages first
                            trimmed_history = '\n'.join(history_lines)
                            history_tokens = self._count_tokens(trimmed_history)
                            trimmed_context["history"] = trimmed_history
                    else:
                        # If we still need to trim, clear history too
                        trimmed_context["history"] = ""
        
        return trimmed_context
    
    def _assemble_prompt(self, state: AIGameState, 
                      narrative_context: Dict[str, Any],
                      memory_context: Dict[str, str],
                      validation_failed: bool) -> str:
        """
        Assemble the prompt for the AI DM with token budgeting
        
        Args:
            state: Current game state
            narrative_context: Narrative context from the NarrativeContextTool
            memory_context: Memory context from LangChain
            validation_failed: Whether validation failed
            
        Returns:
            Assembled prompt template
        """
        # Get current game state and intent
        game_state = state.get("game_state", "exploration")
        intent_data = state.get("intent_data", {})
        intent = intent_data.get("intent", "general")
        
        # Get character data
        character_data = self._get_character_data(state)
        
        # Base system prompt
        system_prompt = self._get_system_prompt(game_state)
        
        # Character information
        character_info = self._get_character_info(character_data)
        
        # Narrative context
        narrative_text = self._get_narrative_context_text(narrative_context, validation_failed)
        
        # Apply token budgeting to memory context
        budgeted_memory = self._apply_token_budget(memory_context, self.memory_context_tokens)
        
        # Memory conflict handling instructions
        conflict_instructions = """
When using the provided context, follow these rules:
1. Prioritize facts from Relevant Documents over conversational Entity summaries if they conflict
2. Facts marked as [Fact] should be treated as canonical information
3. If entity information conflicts, use the most recent or most specific information
"""
        
        # Structured output instructions (if enabled)
        structured_output_instructions = ""
        if self._should_use_structured_output(state):
            structured_output_instructions = """
Include mechanical effects in your response using the following format:
[MECHANICS]
type: damage|healing|condition|resource_change|rest_complete|ability_check|combat_roll
data: {appropriate data for the type}
[/MECHANICS]

You can include multiple [MECHANICS] blocks if needed.
"""
        
        # Combine all sections
        full_prompt = f"""
{system_prompt}

{character_info}

{narrative_text}

{conflict_instructions}

### CONVERSATION HISTORY:
{budgeted_memory['history']}

### KNOWN ENTITIES (CONVERSATIONAL):
{budgeted_memory['entities']}

### RELEVANT KNOWLEDGE & EVENTS:
{budgeted_memory['relevant_docs']}

{structured_output_instructions}

### PLAYER INPUT:
{{player_input}}

### AI DM RESPONSE:
"""
        
        return full_prompt
    
    def _get_system_prompt(self, game_state: str) -> str:
        """Get system prompt based on current game state"""
        base_prompt = """You are a seasoned Dungeon Master for a Dungeons & Dragons 5th Edition game, guiding a solo player through a rich fantasy world. Your role is to weave an immersive, engaging story, staying fully in character as a narrator and arbiter of the world. Respond with vivid descriptions, distinct NPC personalities, and a natural flow that draws the player into the adventure. Adhere strictly to D&D 5e rules, incorporating dice rolls and mechanics only when necessary—blend them seamlessly into the narrative. When D&D 5e rules require a dice roll, prompt the player to roll the die and pause your response there. Do not guess, assume, or simulate the player's roll.

Format your response:
- Use bold for important people, places, and items
- Break long text into paragraphs every 3–4 sentences
- Use Markdown style formatting
- Avoid repeating prior information"""
        
        if game_state == "combat":
            return base_prompt + """

The player is currently in combat. Narrate the scene with high stakes and visceral detail. Manage combat turns: describe the enemy's action, then prompt the player for their move. For dice rolls always prompt the player to roll and stop there. Wait for the player to provide the result before continuing. Keep the pace fast and tense."""
        
        elif game_state == "social":
            return base_prompt + """

The player is in a social interaction. Portray NPCs with distinct personalities, motivations, and speech patterns. Respond to social approaches with appropriate reactions. Give NPCs clear voices, mannerisms, and attitudes. Allow for persuasion, deception, and intimidation attempts."""
        
        elif game_state == "exploration":
            return base_prompt + """

The player is exploring. Describe the environment in rich detail with sensory information and interesting features. Offer clear directions and points of interest. Hint at possible secrets or hidden elements. When perception or investigation checks are needed, prompt for dice rolls."""
        
        elif game_state == "intro":
            return base_prompt + """

This is the beginning of a new adventure. Begin with the character already in an exciting situation. Create a UNIQUE SCENARIO - avoid formulaic openings. Consider the character's background when crafting this opening scene. Establish clear stakes and immediate tension."""
        
        else:
            return base_prompt
    
    def _get_character_info(self, character_data: Optional[Dict[str, Any]]) -> str:
        """Format character information for the prompt"""
        if not character_data:
            return "## CHARACTER INFORMATION:\nNo character data available.\n"
        
        character_info = "## CHARACTER INFORMATION:\n"
        character_info += f"Name: {character_data.get('name', 'Unknown')}\n"
        character_info += f"Race: {character_data.get('race', 'Unknown')}\n"
        character_info += f"Class: {character_data.get('class', character_data.get('character_class', 'Unknown'))}\n"
        character_info += f"Level: {character_data.get('level', 1)}\n"
        character_info += f"Background: {character_data.get('background', 'Unknown')}\n"
        
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
        
        return character_info
    
    def _get_narrative_context_text(self, narrative_context: Dict[str, Any], 
                                  validation_failed: bool) -> str:
        """Format narrative context for the prompt"""
        narrative_text = "## NARRATIVE CONTEXT:\n"
        
        # Location description
        location_description = narrative_context.get("location_description")
        if location_description:
            narrative_text += f"Current Location: {location_description}\n\n"
        
        # Time information
        time_info = narrative_context.get("current_time")
        if time_info:
            narrative_text += f"Current Time: {time_info.get('datetime', 'Unknown')} ({time_info.get('day_phase', 'Unknown')})\n\n"
        
        # Environmental conditions
        env_conditions = narrative_context.get("environmental_conditions", [])
        if env_conditions:
            narrative_text += "Environmental Conditions:\n"
            for condition in env_conditions:
                narrative_text += f"- {condition}\n"
            narrative_text += "\n"
        
        # Active quests
        active_quests = narrative_context.get("active_quests", [])
        if active_quests:
            narrative_text += "Active Quests:\n"
            for quest in active_quests:
                narrative_text += f"- {quest.get('name', 'Unknown Quest')}: {quest.get('objective', '')}\n"
            narrative_text += "\n"
        
        # Add validation failure information if applicable
        if validation_failed:
            validation_result = state.get("validation_result", {})
            reason = validation_result.get("reason", "Action not possible")
            narrative_text += f"## ACTION FAILED:\n{reason}\n\n"
        
        return narrative_text
    
    def _should_use_structured_output(self, state: AIGameState) -> bool:
        """Determine if structured output should be used"""
        # Enable structured output for specific intents or game states
        intent = state.get("intent_data", {}).get("intent", "")
        game_state = state.get("game_state", "")
        
        return (
            intent in ["cast_spell", "weapon_attack", "use_feature", "use_item", "rest"] or
            game_state == "combat"
        )
    
    def _parse_structured_response(self, response_text: str) -> tuple[str, List[Dict[str, Any]]]:
        """
        Parse structured mechanics data from the response
        
        Args:
            response_text: The raw response from the LLM
            
        Returns:
            Tuple of (cleaned_response, mechanics_data)
        """
        mechanics_data = []
        cleaned_response = response_text
        
        # Find all [MECHANICS] blocks
        import re
        mechanics_pattern = r'\[MECHANICS\](.*?)\[/MECHANICS\]'
        matches = re.finditer(mechanics_pattern, response_text, re.DOTALL)
        
        for match in matches:
            mechanics_block = match.group(1).strip()
            
            # Parse the mechanics block
            try:
                lines = mechanics_block.split('\n')
                mechanic = {}
                
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Try to parse data field as JSON
                        if key == 'data':
                            try:
                                value = json.loads(value)
                            except json.JSONDecodeError:
                                # If not valid JSON, treat as string
                                pass
                        
                        mechanic[key] = value
                
                if 'type' in mechanic:
                    mechanics_data.append(mechanic)
            except Exception as e:
                logger.warning(f"Failed to parse mechanics block: {e}")
            
            # Remove the mechanics block from the response
            cleaned_response = cleaned_response.replace(match.group(0), "")
        
        # Clean up extra whitespace
        cleaned_response = re.sub(r'\n{3,}', '\n\n', cleaned_response.strip())
        
        return cleaned_response, mechanics_data
    
    def _get_character_data(self, state: AIGameState) -> Optional[Dict[str, Any]]:
        """Get character data from state or database"""
        character_id = state.get("current_character_id")
        if not character_id:
            return None
        
        # Check if character data is already in state
        if "character_data" in state:
            return state["character_data"]
        
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