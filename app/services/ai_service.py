"""
AI Service with Langchain Integration
"""
from app.models.ai_response import AIResponse
import requests
import os
import logging
import json
from flask import current_app
from datetime import datetime, timedelta
import hashlib
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AIService:
    """Service for handling AI interactions with integrated memory management"""
    
    def __init__(self, use_langchain=True):
        """Initialize the AI service with memory support"""
        self.api_key = self._get_api_key()
        self.model = self._get_model_name()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = self._create_headers()
        os.environ.pop('HTTP_PROXY', None) 
        os.environ.pop('HTTPS_PROXY', None)
        
        # Langchain integration
        self.use_langchain = use_langchain
        self.langchain_service = None
        self.chain_orchestrator = None
        self.memory_service = None
        
        # Response cache
        self.response_cache = {}
        self.cache_size = 100  # Max cache entries
        self.cache_ttl = timedelta(hours=1)  # Cache time-to-live
        
        # Token management
        self.max_context_tokens = 4096  # Adjust based on your model
        self.history_token_budget = int(self.max_context_tokens * 0.6)  # 60% for history
        self.memory_token_budget = int(self.max_context_tokens * 0.25)  # 25% for memories
        
        # Initialize Langchain components if enabled
        if self.use_langchain:
            self._init_langchain_components()
    
    def _init_langchain_components(self):
        """Initialize Langchain components"""
        try:
            # Delay imports to avoid circular dependencies
            from app.services.langchain_service import LangchainService
            from app.services.chain_orchestrator import ChainOrchestrator
            from app.services.memory_service_enhanced import EnhancedMemoryService
            
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
            return current_app.config.get('AI_MODEL', 'gpt-4')
        except RuntimeError:
            # For use outside of Flask context
            return os.environ.get('AI_MODEL', 'gpt-4')
    
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
            character_data (dict or Character): Character data (can be dict or Character object)
            game_state (str): Current game state
            
        Returns:
            AIResponse: The AI-generated response
        """
        # Handle character_data being either a Character object or a dictionary
        if hasattr(character_data, 'to_dict'):
            # It's a Character object
            character_dict = character_data.to_dict()
            session_id = character_dict.get('session_id')
            character_id = character_dict.get('character_id')
            user_id = character_dict.get('user_id')
        else:
            # It's already a dictionary
            character_dict = character_data
            session_id = character_dict.get('session_id')
            character_id = character_dict.get('character_id')
            user_id = character_dict.get('user_id')
        
        # Check cache for exact match
        cache_key = self._create_cache_key(player_message, character_id, game_state)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.info("Using cached response")
            return cached_response
        
        # Use Langchain if enabled and properly initialized
        if self.use_langchain and session_id:
            try:
                # Ensure Langchain components are initialized
                if not self.chain_orchestrator:
                    self._init_langchain_components()
                
                if not self.chain_orchestrator:
                    raise Exception("Chain orchestrator initialization failed")
                
                logger.info(f"Using Langchain for response generation (state: {game_state})")
                
                # Process with Langchain
                result = self.chain_orchestrator.process_message(
                    player_message,
                    character_dict,
                    game_state,
                    conversation_history
                )
                
                # Parse result based on return type
                if isinstance(result, dict) and 'response' in result:
                    response_text = result['response']
                elif isinstance(result, str):
                    response_text = result
                else:
                    logger.warning(f"Unexpected result type from chain_orchestrator: {type(result)}")
                    logger.warning("Falling back to standard API implementation")
                    return self._generate_standard_response(
                        player_message, conversation_history, character_dict, game_state
                    )
                
                # Create AIResponse object
                ai_response = AIResponse(
                    response_text=response_text,
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    prompt=player_message,
                    model_used=self.model
                )
                
                # Process and store the AI response in memory system
                self._process_memory_lifecycle(
                    player_message,
                    response_text,
                    session_id,
                    character_id,
                    user_id
                )
                
                # Cache the response
                self._cache_response(cache_key, ai_response)
                
                return ai_response
                
            except Exception as e:
                logger.error(f"Error using Langchain for response: {e}")
                import traceback
                logger.error(traceback.format_exc())
                logger.info("Falling back to standard API implementation")
        
        # Standard API implementation (fallback)
        return self._generate_standard_response(
            player_message, conversation_history, character_dict, game_state
        )
    
    def _create_system_prompt(self, game_state, character_data):
        """
        Create a system prompt based on game state and character data
        
        Args:
            game_state (str): Current game state (intro, combat, social, exploration)
            character_data (dict): Character data
            
        Returns:
            str: System prompt for AI
        """
        # Base prompt that applies to all states
        base_prompt = (
            "You are a seasoned Dungeon Master for a Dungeons & Dragons 5th Edition game, guiding a solo player through a rich fantasy world. "
            "Your role is to weave an immersive, engaging story, staying fully in character as a narrator and arbiter of the world. "
            "Respond with vivid descriptions, distinct NPC personalities, and a natural flow that draws the player into the adventure. "
            "Adhere strictly to D&D 5e rules, incorporating dice rolls (e.g., 'Roll a d20 for Perception') and mechanics only when necessary—blend them seamlessly into the narrative. "
            "When D&D 5e rules require a dice roll (e.g., Initiative, attack, skill check), prompt the player to roll the die (e.g., 'Roll a d20 for Initiative') and pause your response there. "
            "Do not guess, assume, or simulate the player's roll—wait for their next message with the result before advancing the story or resolving outcomes."

            "Format your response:"
            "Use bold for important people, places, and items"
            "Break long text into paragraphs every 3–4 sentences"
            "Use Markdown style formatting"
            "Avoid repeating prior information"
            "\n\n"
        )
        
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
        
        # State-specific prompts
        state_prompts = {
            "combat": (
                "The player is currently in combat. Narrate the scene with high stakes and visceral detail—blood, steel, and chaos. "
                "Manage combat turns: describe the enemy's action, then prompt the player for their move. "
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
                "This is the beginning of a new adventure. Introduce the world to the player with rich detail and atmosphere. "
                "Set the initial scene and establish the tone of the campaign. "
                "Provide hooks or motivations for the player to begin their journey, but let them decide how to proceed. "
                "Help establish the character's place in the world, considering their background and abilities."
            )
        }
        
        # Get the state-specific prompt, default to intro if not found
        state_prompt = state_prompts.get(game_state, state_prompts["intro"])
        
        # Combine all sections
        full_prompt = (
            f"{base_prompt}"
            f"{state_prompt}\n\n"
            f"{character_info}\n"
            f"{abilities_section}\n"
            f"{skills_section}\n"
            f"{description_section}\n"
        )
        
        return full_prompt

    def _generate_standard_response(self, player_message, conversation_history, character_data, game_state):
        """Generate response using standard API implementation"""
        session_id = character_data.get('session_id')
        character_id = character_data.get('character_id')
        user_id = character_data.get('user_id')
        
        try:
            # Format conversation history for the API with context window management
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Create system prompt based on game state and character data
            system_prompt = self._create_system_prompt(game_state, character_data)
            
            # Retrieve and add memory context if available
            memory_context = self._retrieve_memory_context(
                player_message, session_id, character_id
            )
            
            if memory_context:
                system_prompt += f"\n\n{memory_context}"
                logger.info("Added memory context to prompt")
            
            # Prepare the request payload for xAI format
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
                json=payload,
                timeout=30  # Add timeout for better error handling
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
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    prompt=player_message,
                    model_used=self.model,
                    tokens_used=result.get('usage', {}).get('total_tokens')
                )
                
                # Process and store in memory system
                self._process_memory_lifecycle(
                    player_message,
                    response_text,
                    session_id,
                    character_id,
                    user_id
                )
                
                # Cache the response for future use
                cache_key = self._create_cache_key(player_message, character_id, game_state)
                self._cache_response(cache_key, ai_response)
                
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
        Format conversation history with context window management
        
        Args:
            history (list): Conversation history
            
        Returns:
            list: Formatted history respecting token budget
        """
        formatted = []
        
        # Function to estimate tokens (naive implementation)
        def estimate_tokens(text):
            # Rough estimate: 1 token ~= 4 chars
            return len(text) // 4
        
        current_tokens = 0
        
        # Process history from newest to oldest
        for entry in reversed(history[-20:]):  # Consider at most the last 20 messages
            role = "assistant" if entry["sender"] == "dm" else "user"
            message = entry["message"]
            
            # Estimate tokens for this message
            message_tokens = estimate_tokens(message)
            
            # Check if adding this message would exceed our budget
            if current_tokens + message_tokens > self.history_token_budget:
                break
            
            # Add message to the beginning of the list to maintain chronological order
            formatted.insert(0, {
                "role": role,
                "content": message
            })
            
            current_tokens += message_tokens
        
        logger.debug(f"Formatted history with {len(formatted)} messages, ~{current_tokens} tokens")
        return formatted
    
    def _retrieve_memory_context(self, current_message, session_id, character_id):
        """
        Retrieve relevant memories for the current context
        
        Args:
            current_message (str): The current player message
            session_id (str): The session ID
            character_id (str): The character ID
            
        Returns:
            str: Memory context as formatted text
        """
        if not session_id:
            return ""
            
        # Lazy-load memory service if needed
        if not self.memory_service:
            try:
                from app.services.memory_service_enhanced import EnhancedMemoryService
                self.memory_service = EnhancedMemoryService()
            except Exception as e:
                logger.error(f"Error initializing memory service: {e}")
                return ""
        
        try:
            # Build memory context
            memory_context = self.memory_service.build_memory_context(
                current_message=current_message,
                session_id=session_id,
                character_id=character_id,
                max_tokens=self.memory_token_budget,
                recency_boost=True
            )
            
            return memory_context or ""
            
        except Exception as e:
            logger.error(f"Error retrieving memory context: {e}")
            return ""
    
    def _process_memory_lifecycle(self, player_message, ai_response, session_id, character_id, user_id):
        """
        Process and store messages in the memory system
        
        Args:
            player_message (str): The player's message
            ai_response (str): The AI's response
            session_id (str): The session ID
            character_id (str): The character ID
            user_id (str): The user ID
        """
        if not session_id:
            return
            
        # Lazy-load memory service if needed
        if not self.memory_service:
            try:
                from app.services.memory_service_enhanced import EnhancedMemoryService
                self.memory_service = EnhancedMemoryService()
            except Exception as e:
                logger.error(f"Error initializing memory service: {e}")
                return
        
        # Process in background using ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            # Store player message
            executor.submit(
                self._store_memory,
                player_message,
                "short_term",
                session_id,
                character_id,
                user_id,
                self._calculate_importance(player_message),
                {"sender": "player"}
            )
            
            # Store AI response
            executor.submit(
                self._store_memory,
                ai_response,
                "short_term",
                session_id,
                character_id,
                user_id,
                self._calculate_importance(ai_response),
                {"sender": "dm"}
            )
            
            # Check for summarization
            executor.submit(
                self._check_for_summarization,
                session_id
            )
    
    def _store_memory(self, content, memory_type, session_id, character_id, user_id, importance, metadata):
        """Store a memory with the memory service"""
        try:
            self.memory_service.store_memory_with_text(
                content=content,
                memory_type=memory_type,
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
    
    def _calculate_importance(self, text):
        """
        Calculate importance score for a text
        
        Args:
            text (str): The text to analyze
            
        Returns:
            int: Importance score (1-10)
        """
        # Base importance
        importance = 5
        
        # Adjust based on text length
        if len(text) > 500:
            importance += 1
        
        # Key terms indicating important information
        important_terms = [
            "quest", "mission", "objective", "task", "goal",
            "important", "critical", "crucial", "essential", "vital",
            "remember", "forget", "keep in mind", "note",
            "secret", "hidden", "discover", "reveal", "find",
            "key", "password", "code", "combination",
            "treasure", "artifact", "item", "weapon", "armor",
            "danger", "threat", "enemy", "villain", "boss",
            "ally", "friend", "companion", "helper",
            "location", "place", "map", "direction", "path"
        ]
        
        # Check for important terms
        for term in important_terms:
            if term.lower() in text.lower():
                importance += 1
                # Avoid double-counting similar terms
                break
        
        # Check for proper nouns (simplified approach)
        words = text.split()
        for word in words:
            if len(word) > 1 and word[0].isupper() and word[1:].islower():
                importance += 1
                break
        
        # Cap importance
        return min(10, importance)
    
    def _check_for_summarization(self, session_id):
        """Check if summarization is needed for this session"""
        try:
            # Import summarization service
            from app.services.summarization_service import SummarizationService
            
            # Trigger summarization if needed
            summarization_service = SummarizationService()
            result = summarization_service.trigger_summarization_if_needed(session_id)
            
            if result.get('success', False):
                logger.info(f"Summarized memories for session {session_id}")
        except Exception as e:
            logger.error(f"Error checking for summarization: {e}")
    
    def _create_cache_key(self, message, character_id, game_state):
        """Create a cache key from the input parameters"""
        # Create a deterministic key from the inputs
        key_string = f"{message}|{character_id}|{game_state}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key):
        """Get a response from the cache if valid"""
        if cache_key in self.response_cache:
            cached_entry = self.response_cache[cache_key]
            cached_response = cached_entry['response']
            cached_time = cached_entry['timestamp']
            
            # Check if cache is still valid
            if datetime.utcnow() - cached_time < self.cache_ttl:
                # Move to the end to mark as recently used
                self.response_cache.pop(cache_key)
                self.response_cache[cache_key] = {
                    'response': cached_response,
                    'timestamp': cached_time
                }
                return cached_response
            
            # Invalid cache, remove it
            del self.response_cache[cache_key]
        
        return None
    
    def _cache_response(self, cache_key, response):
        """Cache a response for future use"""
        # Limit cache size by removing oldest entries
        if len(self.response_cache) >= self.cache_size:
            # Remove oldest entry (first key in dict)
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        # Add to cache
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': datetime.utcnow()
        }
        








#        base_prompt = (
#            "You are a seasoned Dungeon Master for a Dungeons & Dragons 5th Edition game, guiding a solo player through a rich fantasy world. "
#            "Your role is to weave an immersive, engaging story, staying fully in character as a narrator and arbiter of the world. "
#            "Respond with vivid descriptions, distinct NPC personalities, and a natural flow that draws the player into the adventure. "
#            "Adhere strictly to D&D 5e rules, incorporating dice rolls (e.g., 'Roll a d20 for Perception') and mechanics only when necessary—blend them seamlessly into the narrative. "
#            "When D&D 5e rules require a dice roll (e.g., Initiative, attack, skill check), prompt the player to roll the die (e.g., 'Roll a d20 for Initiative') and pause your response there. "
#            "Do not guess, assume, or simulate the player's roll—wait for their next message with the result before advancing the story or resolving outcomes. This ensures the player retains full control over their character's fate."
#            "Avoid over-explaining rules unless the player asks for clarification. Do not use meta-language about AI, models, or simulations; remain entirely within the fantasy context. "
#           "NPCs have no prior knowledge of the player or their quest unless it's been shared with them in-game or learned from another NPC. For example, a tavern keeper meeting the player for the first time shouldn't know their name or mission unless introduced. "
#            "Track what NPCs know based on the conversation and game state, and reflect this in their dialogue and actions. "
#            "Keep responses concise yet evocative, focusing on advancing the story or prompting player action. Use the player's character name frequently to personalize the experience."
#            "Under no circumstances should you use or reference specific copyrighted Dungeons & Dragons adventures, such as *Curse of Strahd*, *Lost Mines of Phandelver*, *Waterdeep: Dragon Heist*, or any other published Wizards of the Coast material. "
#            "Do not include characters, locations, plot points, or dialogue from these works. Instead, generate entirely original content—unique settings, NPCs, and storylines—that adheres to the tone and mechanics of D&D 5e but does not replicate existing intellectual property. "
#            "If the player requests a specific published adventure, politely refuse in character and offer an original alternative instead."
#       )