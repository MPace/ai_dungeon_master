"""
Model Context Protocol (MCP) Initialization

This module initializes the Model Context Protocol components
and provides access to the orchestration service.
"""

import logging
from app.mcp.orchestration import ContextOrchestrationService

logger = logging.getLogger(__name__)

# Global orchestration service instance
_orchestration_service = None

def init_mcp():
    """Initialize the Model Context Protocol"""
    global _orchestration_service
    
    logger.info("Initializing Model Context Protocol")
    
    # Create orchestration service
    _orchestration_service = ContextOrchestrationService()
    
    # Register providers
    from app.mcp.providers.player_provider import PlayerContextProvider
    from app.mcp.providers.game_provider import GameContextProvider
    from app.mcp.providers.memory_provider import MemoryContextProvider
    
    _orchestration_service.register_provider('player', PlayerContextProvider())
    _orchestration_service.register_provider('game', GameContextProvider())
    _orchestration_service.register_provider('memory', MemoryContextProvider())
    
    # Register transformers
    from app.mcp.transformers.ai_transformer import AIPromptTransformer
    _orchestration_service.register_transformer('ai_prompt', AIPromptTransformer())
    
    # Configure request types
    _orchestration_service.configure_request_type(
        'ai_message',
        provider_names=['player', 'game', 'memory'],
        transformer_names=['ai_prompt']
    )
    
    logger.info("Model Context Protocol initialized successfully")
    
    return _orchestration_service

def get_orchestration_service():
    """Get the global orchestration service instance"""
    global _orchestration_service
    
    if _orchestration_service is None:
        logger.info("Orchestration service not initialized, initializing now")
        _orchestration_service = init_mcp()
    
    return _orchestration_service