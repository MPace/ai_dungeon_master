"""
AI Service
"""
from app.models.ai_response import AIResponse
import requests
import os
import logging
import json
from flask import current_app

logger = logging.getLogger(__name__)

class AIService:
    """Service for handling AI interactions"""
    
    def __init__(self):
        """Initialize the AI service"""
        self.api_key = current_app.config.get('AI_API_KEY')
        self.model = current_app.config.get('AI_MODEL', 'grok-1')
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.headers = {
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
        try:
            # Format conversation history for the API
            formatted_history = self._format_conversation_history(conversation_history)
            
            # Create system prompt based on game state and character data
            system_prompt = self._create_system_prompt(game_state, character_data)
            
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
                session_id = character_data.get('session_id')
                character_id = character_data.get('character_id')
                user_id = character_data.get('user_id')
                
                ai_response = AIResponse(
                    response_text=response_text,
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    prompt=player_message,
                    model_used=self.model,
                    tokens_used=result.get('usage', {}).get('total_tokens')
                )
                
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
            "You are an expert Dungeon Master for a Dungeons & Dragons 5th Edition game. "
            "Create immersive, engaging responses that follow D&D 5e rules. "
            "Describe environments vividly, represent NPCs with distinct personalities, "
            "and keep the game flowing naturally. "
            "When rules or dice rolls are needed, mention them and incorporate the results into the narrative. "
            "Avoid using meta-language about AI, language models, or the simulation. "
            "Stay fully in character as a Dungeon Master in a fantasy world. "
        )
        
        # Add game state context
        if game_state == "intro":
            base_prompt += (
                "The player is just starting their adventure. Help them get oriented "
                "and excited about the campaign world. Offer hooks to engage them. "
                "Provide vivid descriptions and options for what they might want to do. "
            )
        elif game_state == "combat":
            base_prompt += (
                "The player is in combat. Describe the action vividly and maintain tension. "
                "Track initiative order and enemy actions. Describe combat effects dramatically. "
                "Ask for specific actions, attacks, or spell casting. Mention AC checks and damage rolls when appropriate. "
                "Make combat feel dynamic and consequential. "
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
        
        base_prompt += "\n\nRespond as the Dungeon Master guiding this character through their adventure. Use their character name and reference their abilities, background, and skills where relevant."
        
        return base_prompt