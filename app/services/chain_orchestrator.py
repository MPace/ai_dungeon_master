# app/services/chain_orchestrator.py
"""
Chain Orchestrator
"""
import logging
from typing import Dict, Any, Optional, List
from app.services.langchain_service import LangchainService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class ChainOrchestrator:
    """Orchestrates different Langchain chains for game states"""
    
    def __init__(self, api_key=None):
        """Initialize chain orchestrator"""
        self.langchain_service = LangchainService(api_key=api_key)
        self.ai_service = AIService()
        self.chains = {}
    
    def get_chain_for_state(self, game_state, session_id, character_data):
        """Get or create a chain for the given game state"""
        chain_key = f"{session_id}_{game_state}"
        
        # Return existing chain if available
        if chain_key in self.chains:
            return self.chains[chain_key]
        
        # Create system prompt based on game state
        system_prompt = self._create_system_prompt(game_state, character_data)
        
        # Create chain
        chain = self.langchain_service.create_memory_enhanced_chain(
            system_prompt=system_prompt,
            character_data=character_data,
            session_id=session_id
        )
        
        # Store chain
        self.chains[chain_key] = chain
        
        return chain
    
    def _create_system_prompt(self, game_state, character_data):
        """Create appropriate system prompt based on state"""
        # Use AI service's prompt creation logic for consistency
        return self.ai_service._create_system_prompt(game_state, character_data)
    
    def generate_response(self, message, session_id, character_data, game_state):
        """Generate response using appropriate chain"""
        try:
            # Get chain for this state
            chain = self.get_chain_for_state(game_state, session_id, character_data)
            
            # Run chain
            result = self.langchain_service.run_chain(
                chain=chain,
                message=message,
                session_id=session_id,
                character_id=character_data.get("character_id")
            )
            
            # Wrap in AI response object for compatibility
            from app.models.ai_response import AIResponse
            
            response = AIResponse(
                response_text=result.get("response", ""),
                session_id=session_id,
                character_id=character_data.get("character_id"),
                prompt=message,
                model_used=self.langchain_service.model_name
            )
            
            return response
        except Exception as e:
            logger.error(f"Error generating response with chain: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback to standard AI service
            logger.info("Falling back to standard AI service")
            return self.ai_service.generate_response(
                message, 
                [], 
                character_data, 
                game_state
            )