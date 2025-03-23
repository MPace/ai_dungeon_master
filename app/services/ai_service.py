"""
AI Service with Langchain Integration
"""
from app.models.ai_response import AIResponse
import requests
import os
import logging
import json
from flask import current_app
from langchain.llms import BaseLLM
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from app.services.langchain_service import LangchainService
from app.services.chain_orchestrator import ChainOrchestrator
from app.services.memory_service_enhanced import EnhancedMemoryService

logger = logging.getLogger(__name__)

class AIService:
    """Service for handling AI interactions with optional Langchain support"""
    
    def __init__(self, use_langchain=True):
        """Initialize the AI service"""
        self.api_key = self._get_api_key()
        self.model = self._get_model_name()
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.headers = self._create_headers()
        
        # Langchain integration
        self.use_langchain = use_langchain
        self.langchain_service = None
        self.chain_orchestrator = None
        self.memory_service = None
        
        if self.use_langchain:
            try:
                self.langchain_service = LangchainService(api_key=self.api_key, model_name=self.model)
                self.chain_orchestrator = ChainOrchestrator(api_key=self.api_key)
                self.memory_service = EnhancedMemoryService()
                logger.info(f"Langchain integration initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Langchain: {e}")
                self.use_langchain = False
                logger.info("Falling back to standard API implementation")
    
    def _get_api_key(self):
        """Get API key from app config"""
        try:
            return current_app.config.get('AI_API_KEY')
        except RuntimeError:
            # For use outside of Flask context
            return os.environ.get('AI_API_KEY')
    
    def _get_model_name(self):
        """Get model name from app config"""
        try:
            return current_app.config.get('AI_MODEL', 'grok-2-latest')
        except RuntimeError:
            # For use outside of Flask context
            return os.environ.get('AI_MODEL', 'grok-2-latest')
    
    def _create_headers(self):
        """Create API request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    def generate_response(self, player_message, conversation_history, character_data, game_state="intro"):
        """
        Generate a response from the AI based on the player's message and context
        
        Args:
            player_message (str): The message from the player
            conversation_history (list): List of previous messages
            character_data (dict): Character data
            game_state (str): Current game state
            
        Returns:
            AIResponse: The AI-generated response
        """
        session_id = character_data.get('session_id')
        
        # Use Langchain if enabled and properly initialized
        if self.use_langchain and self.chain_orchestrator and session_id:
            try:
                logger.info(f"Using Langchain for response generation (state: {game_state})")
                response = self.chain_orchestrator.generate_response(
                    player_message,
                    session_id,
                    character_data,
                    game_state
                )
                
                # If we got a valid response, return it
                if response and hasattr(response, 'response_text'):
                    return response
                
                # Otherwise, fall back to standard implementation
                logger.warning("Langchain response generation failed, falling back to standard API")
            except Exception as e:
                logger.error(f"Error using Langchain for response: {e}")
                logger.info("Falling back to standard API implementation")
        
        # Standard API implementation (fallback)
        try:
            # Format conversation history for the API
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Create system prompt based on game state and character data
            system_prompt = self._create_system_prompt(game_state, character_data)
            
            # If memory service is available, enrich the prompt with memories
            if self.memory_service and session_id:
                try:
                    memory_context = self.memory_service.build_memory_context(
                        current_message=player_message,
                        session_id=session_id,
                        character_id=character_data.get('character_id')
                    )
                    
                    if memory_context:
                        system_prompt += f"\n\n{memory_context}"
                        logger.info("Added memory context to prompt")
                except Exception as e:
                    logger.error(f"Error adding memory context: {e}")
            
            # Prepare the request payload - specific to xAI format
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *formatted_history,
                    {"role": "user", "content": player_message}
                ],
                "temperature": 0.7,
                "stream": False
            }
            
            logger.info(f"Sending request to AI API with model: {self.model}")
            
            # Send request to the API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                response_text = result["choices"][0]["message"]["content"]
                
                # Create AIResponse object
                ai_response = AIResponse(
                    response_text=response_text,
                    session_id=character_data.get('session_id'),
                    character_id=character_data.get('character_id'),
                    user_id=character_data.get('user_id'),
                    prompt=player_message,
                    model_used=self.model,
                    tokens_used=result.get('usage', {}).get('total_tokens')
                )
                
                # Store in memory if available
                if self.memory_service and session_id:
                    try:
                        self.memory_service.store_memory_with_text(
                            content=response_text,
                            memory_type="short_term",
                            session_id=session_id,
                            character_id=character_data.get('character_id'),
                            user_id=character_data.get('user_id'),
                            metadata={"sender": "dm"}
                        )
                        
                        # Also store player message
                        self.memory_service.store_memory_with_text(
                            content=player_message,
                            memory_type="short_term",
                            session_id=session_id,
                            character_id=character_data.get('character_id'),
                            user_id=character_data.get('user_id'),
                            metadata={"sender": "player"}
                        )
                    except Exception as e:
                        logger.error(f"Error storing memory: {e}")
                
                return ai_response
            else:
                logger.error(f"Unexpected response format: {result}")
                error_msg = "The Dungeon Master ponders your request. (Unexpected API response format)"
                return AIResponse(response_text=error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with AI API: {e}")
            
            # For 422 errors, try to get more information from the response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"API error details: {error_detail}")
                except:
                    logger.error(f"Could not parse error response. Status code: {e.response.status_code}")
                    
                # Check for common errors
                if e.response.status_code == 422:
                    logger.error("This is likely due to invalid request format or missing required fields")
                elif e.response.status_code == 401:
                    logger.error("Authentication error - check your API key")
                    
            error_msg = "The Dungeon Master seems to be taking a short break. Please try again in a moment."
            return AIResponse(response_text=error_msg)
        
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            error_msg = "The magical connection to the realm seems unstable. The Dungeon Master will return shortly."
            return AIResponse(response_text=error_msg)
    
    def _format_conversation_history(self, history):
        """
        Format conversation history to match API requirements
        
        Args:
            history (list): Conversation history
            
        Returns:
            list: Formatted history
        """
        formatted = []
        
        for entry in history[-10:]:  # Only use the last 10 messages to avoid context overflow
            role = "assistant" if entry["sender"] == "dm" else "user"
            formatted.append({
                "role": role,
                "content": entry["message"]
            })
            
        return formatted
    
    def _create_system_prompt(self, game_state, character_data):
        """
        Create a system prompt based on the current game state and character data
        
        Args:
            game_state (str): Current game state
            character_data (dict): Character data
            
        Returns:
            str: System prompt
        """
        base_prompt = (
            "You are a seasoned Dungeon Master for a Dungeons & Dragons 5th Edition game, guiding a solo player through a rich fantasy world. "
            "Your role is to weave an immersive, engaging story, staying fully in character as a narrator and arbiter of the world. "
            "Respond with vivid descriptions, distinct NPC personalities, and a natural flow that draws the player into the adventure. "
            "Adhere strictly to D&D 5e rules, incorporating dice rolls (e.g., 'Roll a d20 for Perception') and mechanics only when necessary—blend them seamlessly into the narrative. "
            "When D&D 5e rules require a dice roll (e.g., Initiative, attack, skill check), prompt the player to roll the die (e.g., 'Roll a d20 for Initiative') and pause your response there. "
            "Do not guess, assume, or simulate the player's roll—wait for their next message with the result before advancing the story or resolving outcomes. This ensures the player retains full control over their character's fate."
            "Avoid over-explaining rules unless the player asks for clarification. Do not use meta-language about AI, models, or simulations; remain entirely within the fantasy context. "
            "NPCs have no prior knowledge of the player or their quest unless it's been shared with them in-game or learned from another NPC. For example, a tavern keeper meeting the player for the first time shouldn't know their name or mission unless introduced. "
            "Track what NPCs know based on the conversation and game state, and reflect this in their dialogue and actions. "
            "Keep responses concise yet evocative, focusing on advancing the story or prompting player action. Use the player's character name frequently to personalize the experience."
            "Under no circumstances should you use or reference specific copyrighted Dungeons & Dragons adventures, such as *Curse of Strahd*, *Lost Mines of Phandelver*, *Waterdeep: Dragon Heist*, or any other published Wizards of the Coast material. "
            "Do not include characters, locations, plot points, or dialogue from these works. Instead, generate entirely original content—unique settings, NPCs, and storylines—that adheres to the tone and mechanics of D&D 5e but does not replicate existing intellectual property. "
            "If the player requests a specific published adventure, politely refuse in character and offer an original alternative instead."
        )
        
        # Add game state context
        if game_state == "intro":
            base_prompt += (
                "The player is just starting their adventure. Help them get oriented "
                "and excited about the campaign world. Offer hooks to engage them. "
                "Provide vivid descriptions and let them decide what they might want to do. "
            )
        elif game_state == "combat":
            base_prompt += (
                "The player is locked in battle. Narrate the scene with high stakes and visceral detail—blood, steel, and chaos. "
                "Manage combat turns: describe the enemy's last action, then prompt the player for their move (e.g., 'The orc swings its axe; what do you do?'). "
                "For dice rolls like initiative, attack rolls, or saves, always prompt the player to roll (e.g., 'Roll a d20 for Initiative') and stop there—do not assume or simulate the player's roll under any circumstances. "
                "Wait for the player to provide the result in their next message before continuing the combat sequence. Only resolve enemy actions or outcomes after the player's input is received. "
                "Keep the pace fast and tense, but respect the player's agency over their rolls."
            )
        elif game_state == "exploration":
            base_prompt += (
                "The player is exploring. Describe the environment in rich detail. "
                "Include sensory information and interesting features that reward investigation. "
                "Offer clear directions and points of interest. Hint at possible secrets or hidden elements. "
                "Create a sense of wonder and discovery. "
            )
        elif game_state == "social":
            base_prompt += (
                "The player is in a social interaction. Portray NPCs with distinct personalities, "
                "motivations, and speech patterns. Respond to social approaches and charisma-based actions. "
                "Give NPCs clear voices, mannerisms, and attitudes. "
                "Allow for persuasion, deception, and intimidation attempts where appropriate. "
            )
        
        # Add character context if available
        if character_data:
            base_prompt += "\n\n## CHARACTER INFORMATION:"
            
            # Basic character info
            if character_data.get("name"):
                base_prompt += f"\nName: {character_data['name']}"
            if character_data.get("race"):
                race_key = character_data["race"]
                race_name = race_key.capitalize()
                base_prompt += f"\nRace: {race_name}"
            if character_data.get("class"):
                class_key = character_data["class"]
                class_name = class_key.capitalize()
                base_prompt += f"\nClass: {class_name}"
            if character_data.get("level"):
                base_prompt += f"\nLevel: {character_data['level']}"
            if character_data.get("background"):
                background_key = character_data["background"]
                background_name = background_key.capitalize()
                base_prompt += f"\nBackground: {background_name}"
                
            # Add abilities if available
            if character_data.get("abilities"):
                base_prompt += "\n\nAbility Scores:"
                for ability, score in character_data["abilities"].items():
                    modifier = (score - 10) // 2
                    sign = "+" if modifier >= 0 else ""
                    base_prompt += f"\n- {ability.capitalize()}: {score} ({sign}{modifier})"
            
            # Add skills if available
            if character_data.get("skills") and len(character_data["skills"]) > 0:
                base_prompt += "\n\nSkill Proficiencies:"
                for skill in character_data["skills"]:
                    base_prompt += f"\n- {skill}"
            
            # Add character description if available
            if character_data.get("description"):
                base_prompt += f"\n\nDescription: {character_data['description']}"
        
        base_prompt += "\n\nRespond as the Dungeon Master guiding this character through their adventure. Use their character name."
        
        return base_prompt
    
    def create_langchain_prompt_template(self, game_state, character_data):
        """
        Create a Langchain prompt template for a given game state
        
        Args:
            game_state (str): Current game state
            character_data (dict): Character data
            
        Returns:
            PromptTemplate: Langchain prompt template
        """
        # Create base system prompt
        system_prompt = self._create_system_prompt(game_state, character_data)
        
        # Add placeholders for Langchain
        template = f"{system_prompt}\n\n{{memory_context}}\n\n{{history}}\n\nPlayer: {{input}}\nDM:"
        
        # Create template
        prompt_template = PromptTemplate(
            input_variables=["memory_context", "history", "input"],
            template=template
        )
        
        return prompt_template
    
    def create_chain_for_state(self, game_state, character_data, session_id):
        """
        Create a Langchain chain for a specific game state
        
        Args:
            game_state (str): Game state
            character_data (dict): Character data
            session_id (str): Session ID
            
        Returns:
            LLMChain: Langchain chain for this state
        """
        if not self.langchain_service:
            logger.error("Langchain service not initialized")
            return None
        
        try:
            # Create prompt template
            prompt_template = self.create_langchain_prompt_template(game_state, character_data)
            
            # Create chain
            chain = self.langchain_service.create_memory_enhanced_chain(
                system_prompt=prompt_template.template,
                character_data=character_data,
                session_id=session_id
            )
            
            return chain
        except Exception as e:
            logger.error(f"Error creating chain for state {game_state}: {e}")
            return None