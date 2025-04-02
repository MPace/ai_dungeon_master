"""
Chain Orchestrator for AI Dungeon Master

This module orchestrates the Langchain components for the AI Dungeon Master,
managing the flow of information between different chains and components.
"""
import logging
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI

logger = logging.getLogger(__name__)

class ChainOrchestrator:
    """Orchestrates Langchain components for AI Dungeon Master"""
    
    def __init__(self, api_key=None, model_name="gpt-4"):
        """
        Initialize the orchestrator with Langchain components
        
        Args:
            api_key (str, optional): API key for the LLM service
            model_name (str): Name of the model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.llm = None
        
        # Initialize memory service
        from app.services.memory_service_enhanced import EnhancedMemoryService
        self.memory_service = EnhancedMemoryService()
        
        # Initialize different chains for different game states
        self.intro_chain = None
        self.combat_chain = None
        self.social_chain = None
        self.exploration_chain = None
        
        # Initialize the chains
        self._initialize_chains()

    def _initialize_chains(self):
        """Initialize all the chains with appropriate templates"""
        try:
            # Initialize LLM
            self.llm = OpenAI(
                temperature=0.7,
                model_name=self.model_name,
                api_key=self.api_key
            )
            
            # Initialize chain templates
            self._init_intro_chain()
            self._init_combat_chain()
            self._init_social_chain()
            self._init_exploration_chain()
            
            logger.info("Chain orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing chains: {e}")
            raise

    def _init_intro_chain(self):
        """Initialize the intro chain"""
        template = """
        You are a skilled Dungeon Master for a D&D 5e game. Create an engaging introduction for a new player.
        
        Character Information:
        Name: {character_name}
        Race: {character_race}
        Class: {character_class}
        Background: {character_background}
        
        {memory_context}
        
        Previous conversation:
        {history}
        
        User message: {input}
        
        DM response:
        """
        
        prompt = PromptTemplate(
            input_variables=["character_name", "character_race", "character_class", 
                            "character_background", "memory_context", "history", "input"],
            template=template
        )
        
        self.intro_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True
        )

    def _init_combat_chain(self):
        """Initialize the combat chain"""
        template = """
        You are a skilled Dungeon Master for a D&D 5e game. The player is currently in combat.
        
        Character Information:
        Name: {character_name}
        Race: {character_race}
        Class: {character_class}
        Background: {character_background}
        
        {memory_context}
        
        Previous conversation:
        {history}
        
        User message: {input}
        
        DM response: (Focus on exciting, detailed combat and use D&D 5e rules accurately)
        """
        
        prompt = PromptTemplate(
            input_variables=["character_name", "character_race", "character_class", 
                            "character_background", "memory_context", "history", "input"],
            template=template
        )
        
        self.combat_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True
        )

    def _init_social_chain(self):
        """Initialize the social chain"""
        template = """
        You are a skilled Dungeon Master for a D&D 5e game. The player is currently in a social interaction.
        
        Character Information:
        Name: {character_name}
        Race: {character_race}
        Class: {character_class}
        Background: {character_background}
        
        {memory_context}
        
        Previous conversation:
        {history}
        
        User message: {input}
        
        DM response: (Focus on rich character interactions, dialogue, and social dynamics)
        """
        
        prompt = PromptTemplate(
            input_variables=["character_name", "character_race", "character_class", 
                            "character_background", "memory_context", "history", "input"],
            template=template
        )
        
        self.social_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True
        )

    def _init_exploration_chain(self):
        """Initialize the exploration chain"""
        template = """
        You are a skilled Dungeon Master for a D&D 5e game. The player is currently exploring.
        
        Character Information:
        Name: {character_name}
        Race: {character_race}
        Class: {character_class}
        Background: {character_background}
        
        {memory_context}
        
        Previous conversation:
        {history}
        
        User message: {input}
        
        DM response: (Focus on vivid descriptions, discoveries, and environmental interactions)
        """
        
        prompt = PromptTemplate(
            input_variables=["character_name", "character_race", "character_class", 
                            "character_background", "memory_context", "history", "input"],
            template=template
        )
        
        self.exploration_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True
        )
    
    def process_message(self, message, character_data, game_state="intro", session_id=None, user_id=None):
        """
        Process a message using the appropriate chain based on the game state
        
        Args:
            message (str): The user's message
            character_data (dict): Character data
            game_state (str): Current game state
            session_id (str): The session ID
            user_id (str): The user ID
            
        Returns:
            str: The response from the AI
        """
        try:
            # Create memory for this session
            from app.services.langchain_memory import VectorDBMemory
            
            memory = VectorDBMemory(
                memory_service=self.memory_service,
                session_id=session_id,
                character_id=character_data.get('character_id'),
                user_id=user_id,
                memory_key="history",
                input_key="input",
                context_key="memory_context"
            )
            
            # Prepare inputs for the chain
            inputs = {
                "character_name": character_data.get('name', 'Unknown'),
                "character_race": character_data.get('race', 'Unknown'),
                "character_class": character_data.get('class', 'Unknown'),
                "character_background": character_data.get('background', 'Unknown'),
                "input": message,
            }
            
            # Select the appropriate chain based on game state
            if game_state == "combat":
                chain = self.combat_chain
            elif game_state == "social":
                chain = self.social_chain
            elif game_state == "exploration":
                chain = self.exploration_chain
            else:  # Default to intro chain
                chain = self.intro_chain
            
            # Set the memory for the chain
            chain.memory = memory
            logger.info(f"Using chain for game state: {game_state} with VectorDBMemory")

            if hasattr(memory, 'memory_service'):
                logger.info(f"Memory service used: {memory.memory_service.__class__.__name__}")
            
            # Run the chain
            response = chain.run(**inputs)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error processing message with chain: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Provide a fallback response
            return "The Dungeon Master seems momentarily distracted. Please try again."