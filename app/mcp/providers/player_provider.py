"""
Player Context Provider

This module provides the implementation of the player context provider,
which retrieves player and character information for the MCP.
"""

import logging
from typing import Dict, Any
from app.mcp.interfaces import IContextProvider, BaseContext
from app.mcp.context_objects import PlayerContext
from app.services.character_service import CharacterService

logger = logging.getLogger(__name__)

class PlayerContextProvider(IContextProvider):
    """
    Provider for player context
    
    This provider retrieves player and character information
    from the character service.
    """
    
    def get_context(self, request_data: Dict[str, Any]) -> BaseContext:
        """
        Retrieve player context based on request data
        
        Args:
            request_data: Data required to retrieve the context
                Must contain 'user_id' and may contain 'character_id'
                
        Returns:
            PlayerContext: The player context
        """
        logger.info("Retrieving player context")
        
        # Extract required data
        user_id = request_data.get('user_id')
        if user_id is None:
            logger.error("Missing required user_id in request data")
            raise ValueError("Missing required user_id in request data")
        
        # Character ID may be provided directly or retrieved from user data
        character_id = request_data.get('character_id')
        
        # Get character data if ID is provided
        character_data = {}
        if character_id:
            try:
                logger.debug(f"Getting character data for character_id: {character_id}")
                result = CharacterService.get_character(character_id, user_id)
                
                if result and result.get('success') and result.get('character'):
                    character = result.get('character')
                    # Convert to dictionary if it's an object
                    if hasattr(character, 'to_dict'):
                        character_data = character.to_dict()
                    else:
                        character_data = character
                        
                    logger.debug(f"Character data retrieved for: {character_data.get('name', 'Unknown')}")
                else:
                    logger.warning(f"Character not found: {character_id}")
            except Exception as e:
                logger.error(f"Error retrieving character data: {e}")
        else:
            # If no character_id provided, try to get the user's first character
            try:
                logger.debug(f"No character_id provided, getting first character for user: {user_id}")
                result = CharacterService.list_characters(user_id)
                
                if result and result.get('success') and result.get('characters'):
                    characters = result.get('characters')
                    if characters:
                        character = characters[0]
                        # Convert to dictionary if it's an object
                        if hasattr(character, 'to_dict'):
                            character_data = character.to_dict()
                            character_id = character_data.get('character_id')
                        else:
                            character_data = character
                            character_id = character.get('character_id')
                            
                        logger.debug(f"First character retrieved: {character_data.get('name', 'Unknown')}")
                    else:
                        logger.warning(f"No characters found for user: {user_id}")
                else:
                    logger.warning(f"Failed to retrieve characters for user: {user_id}")
            except Exception as e:
                logger.error(f"Error retrieving user's characters: {e}")
        
        # Create player context
        logger.info(f"Creating player context for user_id: {user_id}, character_id: {character_id}")
        context = PlayerContext(
            user_id=user_id,
            character_id=character_id,
            character_data=character_data
        )
        
        return context