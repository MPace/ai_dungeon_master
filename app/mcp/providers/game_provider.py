"""
Game Context Provider

This module provides the implementation of the game context provider,
which retrieves game state, entities, and environment information for the MCP.
"""

import logging
from typing import Dict, Any
from app.mcp.interfaces import IContextProvider, BaseContext
from app.mcp.context_objects import GameContext
from app.services.game_service import GameService

logger = logging.getLogger(__name__)

class GameContextProvider(IContextProvider):
    """
    Provider for game context
    
    This provider retrieves game state information including the current
    game state, entities, environment, and player decisions.
    """
    
    def get_context(self, request_data: Dict[str, Any]) -> BaseContext:
        """
        Retrieve game context based on request data
        
        Args:
            request_data: Data required to retrieve the context
                Must contain 'session_id' and 'user_id'
                
        Returns:
            GameContext: The game context
        """
        logger.info("Retrieving game context")
        
        # Extract required data
        session_id = request_data.get('session_id')
        user_id = request_data.get('user_id')
        
        if not session_id:
            logger.warning("No session_id provided in request data")
            # Return empty context if no session ID
            return GameContext()
            
        if not user_id:
            logger.error("Missing required user_id in request data")
            raise ValueError("Missing required user_id in request data")
        
        # Get session data
        game_state = 'intro'  # Default state
        entities = {}
        environment = {}
        player_decisions = []
        
        try:
            logger.debug(f"Getting session data for session_id: {session_id}")
            result = GameService.get_session(session_id, user_id)
            
            if result and result.get('success') and result.get('session'):
                session = result.get('session')
                
                # Convert to dictionary if it's an object
                if hasattr(session, 'to_dict'):
                    session_data = session.to_dict()
                else:
                    session_data = session
                
                # Extract relevant data
                game_state = session_data.get('game_state', 'intro')
                
                # Get entities
                entities_result = GameService.get_important_entities(session_id, user_id)
                if entities_result and entities_result.get('success'):
                    entities = entities_result.get('entities', {})
                
                # Extract player decisions if available
                player_decisions = session_data.get('player_decisions', [])
                
                # Extract or create environment data
                # This could be expanded based on your game's specific needs
                environment = {
                    'state': game_state,
                    'time_of_day': session_data.get('time_of_day', 'day'),
                    'location': session_data.get('location', 'unknown'),
                    'weather': session_data.get('weather', 'clear')
                }
                
                logger.debug(f"Session data retrieved, game_state: {game_state}")
            else:
                logger.warning(f"Session not found: {session_id}")
        except Exception as e:
            logger.error(f"Error retrieving session data: {e}")
        
        # Create game context
        logger.info(f"Creating game context for session_id: {session_id}, game_state: {game_state}")
        context = GameContext(
            session_id=session_id,
            game_state=game_state,
            entities=entities,
            environment=environment,
            player_decisions=player_decisions
        )
        
        return context