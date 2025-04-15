"""
AI Service with Langchain Integration and Model Context Protocol
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
from app.extensions import get_db

# New MCP imports
from app.mcp import get_orchestration_service
from app.mcp.context_objects import AIPromptContext
from app.mcp.transformers.ai_transformer import AIPromptTransformer

logger = logging.getLogger(__name__)



class AIService:
    """Service for handling AI interactions with integrated memory management"""
    
    def __init__(self, use_langchain=True):
    # Initialize the AI service with memory support and MCP
        self.api_key = self._get_api_key()
        self.model = self._get_model_name()
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = self._create_headers()
        
        
        # Langchain integration
        self.use_langchain = use_langchain
        self.langchain_service = None
        self.chain_orchestrator = None
        self.memory_service = None
        
        # MCP integration
        self.use_mcp = True  # Flag to enable/disable MCP
        self.context_orchestrator = None
        
        # Response cache
        self.response_cache = {}
        self.cache_size = 100  # Max cache entries
        self.cache_ttl = timedelta(hours=1)  # Cache time-to-live
        
        # Token management
        self.max_context_tokens = 4096  # Adjust based on your model
        self.history_token_budget = int(self.max_context_tokens * 0.6)  # 60% for history
        self.memory_token_budget = int(self.max_context_tokens * 0.25)  # 25% for memories
        
        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all service components"""
        # Initialize Langchain components if enabled
        if self.use_langchain:
            self._init_langchain_components()
        
        # Initialize MCP if enabled
        if self.use_mcp:
            self._init_mcp_components()

    def _init_mcp_components(self):
        """Initialize Model Context Protocol components"""
        try:
            # Get the orchestration service
            self.context_orchestrator = get_orchestration_service()
            logger.info("MCP components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP components: {e}")
            self.use_mcp = False
            logger.info("MCP has been disabled due to initialization failure")
    
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
    
    def normalize_character_data(character_data):
        """
        Normalize character data to ensure compatibility with AI service.
        Handles both Character objects and dictionaries from different sources.
        
        Args:
            character_data: Character object or dictionary
            
        Returns:
            dict: Normalized character data dictionary
        """
        # Convert Character object to dictionary if needed
        if hasattr(character_data, 'to_dict'):
            char_dict = character_data.to_dict()
        else:
            char_dict = character_data.copy() if character_data else {}
        
        # Ensure all required fields are present with proper naming
        normalized = {
            'name': char_dict.get('name') or char_dict.get('characterName') or 'Unknown',
            'race': char_dict.get('race') or char_dict.get('raceName') or 'Unknown',
            'class': char_dict.get('class') or char_dict.get('character_class') or char_dict.get('className') or 'Fighter',
            'background': char_dict.get('background') or char_dict.get('backgroundName') or 'Acolyte',
            'level': char_dict.get('level', 1),
            'abilities': char_dict.get('abilities') or char_dict.get('finalAbilityScores') or {
                'strength': 10,
                'dexterity': 10,
                'constitution': 10,
                'intelligence': 10,
                'wisdom': 10,
                'charisma': 10
            },
            'skills': [],
            'character_id': char_dict.get('character_id') or char_dict.get('characterId'),
            'user_id': char_dict.get('user_id'),
            'description': char_dict.get('description') or ''
        }
        
        # Extract skills from different possible locations
        if 'skills' in char_dict and isinstance(char_dict['skills'], list):
            normalized['skills'] = char_dict['skills']
        elif 'proficiencies' in char_dict and isinstance(char_dict['proficiencies'], dict):
            if 'skills' in char_dict['proficiencies'] and isinstance(char_dict['proficiencies']['skills'], list):
                normalized['skills'] = char_dict['proficiencies']['skills']
        
        # Ensure hit points are correctly mapped
        normalized['hit_points'] = char_dict.get('hit_points') or char_dict.get('hitPoints') or {}
        if not normalized['hit_points'] and 'calculatedStats' in char_dict:
            hp_value = char_dict['calculatedStats'].get('hitPoints')
            if hp_value:
                normalized['hit_points'] = {'max': hp_value, 'current': hp_value}
        
        # Add any other fields from the original data
        for key, value in char_dict.items():
            if key not in normalized:
                normalized[key] = value
        
        return normalized
    
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
        # Normalize character data
        character_dict = self.normalize_character_data(character_data)

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
        
        # Determine which approach to use
        if self.use_mcp and self.context_orchestrator:
            logger.info("Using MCP for response generation")
            return self._generate_mcp_response(
                player_message, conversation_history, character_dict, 
                session_id, character_id, user_id, game_state
            )
        elif self.use_langchain and self.chain_orchestrator:
            logger.info("Using Langchain for response generation")
            # [Existing Langchain code]
            # ...
        else:
            logger.info("Using standard API for response generation")
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
            
            # Retrieve and add memory context
            memory_result = self._retrieve_memory_context(
                player_message, session_id, character_id
            )
            
            # Check if memory retrieval is async
            memory_context = ""
            if memory_result.get("success", False):
                if memory_result.get("async", False):
                    # Wait for memory retrieval task to complete (max 10 seconds)
                    from celery.result import AsyncResult
                    task_id = memory_result.get("task_id")
                    task = AsyncResult(task_id)
                    
                    try:
                        # Wait for a result with timeout
                        task_result = task.get(timeout=10)
                        if task_result and task_result.get("success", False):
                            memory_context = task_result.get("memory_context", "")
                            logger.info("Retrieved memory context from async task")
                    except Exception as task_e:
                        logger.warning(f"Timeout or error waiting for memory task: {task_e}")
                        # Proceed without memory context
                else:
                    # Synchronous result
                    memory_context = memory_result.get("memory_context", "")
            
            # Add memory context to prompt if available
            if memory_context:
                system_prompt += f"\n\n{memory_context}"
                logger.info("Added memory context to prompt")
            
            # Prepare the request payload
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
                timeout=30
            )
        
        # [Rest of the method remains the same...]
            
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
        """
        if not session_id:
            return {"success": False, "error": "No session ID provided", "memory_context": ""}
                
        # Lazy-load memory service if needed
        if not self.memory_service:
            try:
                from app.services.memory_service_enhanced import EnhancedMemoryService
                self.memory_service = EnhancedMemoryService()
            except Exception as e:
                logger.error(f"Error initializing memory service: {e}")
                return {"success": False, "error": str(e), "memory_context": ""}
        
        try:
            # Get embedding service
            from app.extensions import get_embedding_service
            embedding_service = get_embedding_service()
            if embedding_service is None:
                logger.error("Embedding service not available")
                return {"success": False, "error": "Embedding service not available", "memory_context": ""}
            
            # Generate embedding for query
            query_embedding = embedding_service.generate_embedding(current_message)
            
            # Direct vector retrieval - use embedding services directly
            from app.extensions import get_db
            db = get_db()
            if db is None:
                return {"success": False, "error": "Database connection failed", "memory_context": ""}
                
            # Log vector retrieval attempt
            logger.info(f"Retrieving memories via vector similarity for session {session_id}")
            
            # Explicitly use vector search
            memory_context = self.memory_service.build_memory_context(
                current_message=current_message,
                session_id=session_id,
                character_id=character_id,
                max_tokens=self.memory_token_budget
            )
            
            logger.info(f"Retrieved memory context: {memory_context[:100]}...")
            
            return {
                "success": True,
                "async": False,
                "memory_context": memory_context
            }
                
        except Exception as e:
            logger.error(f"Error retrieving memory context: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "memory_context": ""}
    
    def _process_memory_lifecycle(self, player_message, ai_response, session_id, character_id, user_id):
        """Process and store messages in the memory system"""
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
        
        # Calculate message importance
        player_importance = self._calculate_importance(player_message)
        ai_importance = self._calculate_importance(ai_response)
        
        # Store player message
        player_result = self.memory_service.store_memory_with_text(
            content=player_message,
            memory_type='short_term',
            session_id=session_id,
            character_id=character_id,
            user_id=user_id,
            importance=player_importance,
            metadata={"sender": "player"},
            async_mode=False  # Use synchronous mode for reliability
        )
        
        # Store AI response
        ai_result = self.memory_service.store_memory_with_text(
            content=ai_response,
            memory_type='short_term',
            session_id=session_id,
            character_id=character_id,
            user_id=user_id,
            importance=ai_importance,
            metadata={"sender": "dm"},
            async_mode=False  # Use synchronous mode for reliability
        )
        
        # Check if high-importance memory should be promoted to long-term
        if player_importance >= 8 or ai_importance >= 8:
            if player_importance >= 8 and player_result.get('success') and player_result.get('memory'):
                # Promote player message to long-term memory
                self.memory_service.promote_to_long_term(player_result['memory'].memory_id)
                
            if ai_importance >= 8 and ai_result.get('success') and ai_result.get('memory'):
                # Promote AI response to long-term memory
                self.memory_service.promote_to_long_term(ai_result['memory'].memory_id)
        
        # Check if summarization is needed (e.g., every 10 messages)
        try:
            db = get_db()
            if db is not None:
                session_data = db.sessions.find_one({'session_id': session_id})
                if session_data and 'history' in session_data:
                    # Check if message count is a multiple of 10
                    if len(session_data['history']) % 10 == 0 and len(session_data['history']) > 0:
                        # Trigger summarization
                        from app.services.game_service import GameService
                        from app.models.game_session import GameSession
                        session_obj = GameSession.from_dict(session_data)
                        GameService._update_session_summary_if_needed(session_obj)
        except Exception as e:
            logger.error(f"Error checking for summarization: {e}")
        
    
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

    def _generate_mcp_response(self, player_message, conversation_history, character_data, 
                      session_id, character_id, user_id, game_state):
        """
        Generate a response using the Model Context Protocol
        
        Args:
            player_message (str): The message from the player
            conversation_history (list): List of previous messages
            character_data (dict): Character data as a dictionary
            session_id (str): The session ID
            character_id (str): The character ID
            user_id (str): The user ID
            game_state (str): Current game state
            
        Returns:
            AIResponse: The AI-generated response
        """
        try:
            # Build memory context directly 
            memory_context = ""
            if self.memory_service is None:
                try:
                    from app.services.memory_service_enhanced import EnhancedMemoryService
                    self.memory_service = EnhancedMemoryService()
                except Exception as e:
                    logger.error(f"Error initializing memory service: {e}")
            
            if self.memory_service:
                memory_context = self.memory_service.build_memory_context(
                    current_message=player_message,
                    session_id=session_id,
                    character_id=character_id,
                    max_tokens=self.memory_token_budget
                )
            
            # Prepare request data for context building
            request_data = {
                'session_id': session_id,
                'user_id': user_id,
                'character_id': character_id,
                'message': player_message,
                'game_state': game_state,
                'history': conversation_history,
                'memory_context': memory_context
            }
        
            
            # Build context for AI message
            context = self.context_orchestrator.build_context('ai_message', request_data)
            
            # Ensure we have AIPromptContext
            if not isinstance(context, AIPromptContext):
                logger.warning(f"Expected AIPromptContext but got {type(context).__name__}")
                # Convert using transformer
                transformer = AIPromptTransformer()
                context = transformer.transform(context)
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": context.system_prompt}
            ]
            
            # Add character context if available
            if context.character_context:
                messages.append({"role": "system", "content": context.character_context})
            
            # Add game context if available
            if context.game_context:
                messages.append({"role": "system", "content": context.game_context})
            
            # Add memory context if available
            if context.memory_context:
                messages.append({"role": "system", "content": context.memory_context})
            
            # Add conversation history
            for entry in self._format_conversation_history(conversation_history):
                messages.append(entry)
            
            # Add current message
            messages.append({"role": "user", "content": player_message})
            
            logger.info(f"Sending request to AI API with model: {self.model} using MCP")
            
            # Send request to the API
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
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
        
        except Exception as e:
            logger.error(f"Error generating response with MCP: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fall back to standard response generation
            return self._generate_standard_response(
                player_message, conversation_history, character_data, game_state
            )
        








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