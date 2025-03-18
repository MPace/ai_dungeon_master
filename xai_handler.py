"""
Specialized handler for the xAI (Grok) API
"""

import os
import requests
import json
from typing import Dict, List, Any, Optional

class XAIHandler:
    """
    Handles communication with xAI/Grok API for generating D&D game responses
    """
    def __init__(self, api_key: str, model: str = None):
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.api_key = api_key
        self.model = model or "grok-1"  # Default to grok-1 if no model specified
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
    def generate_response(self, 
                         player_message: str, 
                         conversation_history: List[Dict[str, Any]],
                         character_data: Optional[Dict[str, Any]] = None,
                         game_state: str = "intro") -> str:
        """
        Generate a response from the xAI API based on the player's message,
        conversation history, character data, and game state.
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
                "stream": False  # Important for xAI API
            }
            
            print(f"Sending request to xAI API with model: {self.model}")
            
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
                return result["choices"][0]["message"]["content"]
            else:
                print(f"Unexpected response format: {result}")
                return "The Dungeon Master ponders your request. (Unexpected API response format)"
                
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with xAI API: {e}")
            # For 422 errors, try to get more information from the response
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"API error details: {error_detail}")
                except:
                    print(f"Could not parse error response. Status code: {e.response.status_code}")
                    
                # Check for common errors
                if e.response.status_code == 422:
                    print("This is likely due to invalid request format or missing required fields")
                elif e.response.status_code == 401:
                    print("Authentication error - check your API key")
                    
            return "The Dungeon Master seems to be taking a short break. Please try again in a moment."
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return "The magical connection to the realm seems unstable. The Dungeon Master will return shortly."
    
    def _format_conversation_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history to match API requirements"""
        formatted = []
        
        for entry in history[-10:]:  # Only use the last 10 messages to avoid context overflow
            role = "assistant" if entry["sender"] == "dm" else "user"
            formatted.append({
                "role": role,
                "content": entry["message"]
            })
            
        return formatted
    
    def _create_system_prompt(self, game_state: str, character_data: Optional[Dict[str, Any]]) -> str:
        """Create a system prompt based on the current game state and character data"""
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
                # Add special race info if available from the frontend (not passed directly)
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