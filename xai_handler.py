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
            print(f"Request payload: {json.dumps(payload, indent=2)}")
            
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
            
            print(f"Response received: {json.dumps(result, indent=2)}")
            
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
        )
        
        # Add game state context
        if game_state == "intro":
            base_prompt += (
                "The player is just starting their adventure. Help them get oriented "
                "and excited about the campaign world. Offer hooks to engage them."
            )
        elif game_state == "combat":
            base_prompt += (
                "The player is in combat. Describe the action vividly and maintain tension. "
                "Track initiative order and enemy actions. Describe combat effects dramatically."
            )
        elif game_state == "exploration":
            base_prompt += (
                "The player is exploring. Describe the environment in rich detail. "
                "Include sensory information and interesting features that reward investigation."
            )
        elif game_state == "social":
            base_prompt += (
                "The player is in a social interaction. Portray NPCs with distinct personalities, "
                "motivations, and speech patterns. Respond to social approaches and charisma-based actions."
            )
        
        # Add character context if available
        if character_data:
            char_details = []
            if "name" in character_data:
                char_details.append(f"Name: {character_data['name']}")
            if "race" in character_data:
                char_details.append(f"Race: {character_data['race']}")
            if "class" in character_data:
                char_details.append(f"Class: {character_data['class']}")
            if "level" in character_data:
                char_details.append(f"Level: {character_data['level']}")
                
            if char_details:
                char_info = ", ".join(char_details)
                base_prompt += f"\n\nThe player's character is: {char_info}."
                
            # Add abilities if available
            if "abilities" in character_data:
                base_prompt += "\nCharacter ability scores: "
                for ability, score in character_data["abilities"].items():
                    base_prompt += f"{ability}: {score}, "
                    
        return base_prompt